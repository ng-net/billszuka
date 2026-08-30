from typing import Any
from fastapi import APIRouter, Header, HTTPException
import urllib.request
import urllib.error
import asyncio

from pathlib import Path

import db
import api_server

router = APIRouter()

def check_quota(user: str, new_bytes: int):
    total_bytes = 0
    with db.connect() as conn:
        rows = conn.execute("SELECT size_bytes FROM catalog_files WHERE uploaded_by=?", (user,)).fetchall()
        total_bytes += sum(r["size_bytes"] for r in rows)
    
    items = api_server._read_knowledge_index()
    for item in items:
        if item.get("uploaded_by") == user:
            total_bytes += item.get("size", 0)
            
    if total_bytes + new_bytes > 500 * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Upload would exceed 500MB quota. Usage: {total_bytes / 1024 / 1024:.1f} MB.")

@router.get("/api/files")
async def get_my_files(x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User")) -> dict[str, Any]:
    user = api_server._require_user(x_billszuka_user)
    out = []
    total_bytes = 0
    
    # Catalogs
    with db.connect() as conn:
        rows = conn.execute("SELECT filename, uploaded_at, size_bytes FROM catalog_files WHERE uploaded_by=?", (user,)).fetchall()
        for r in rows:
            out.append({"type": "catalog", "filename": r["filename"], "uploaded_at": r["uploaded_at"], "size_bytes": r["size_bytes"]})
            total_bytes += r["size_bytes"]

    # Knowledge
    items = api_server._read_knowledge_index()
    for item in items:
        if item.get("uploaded_by") == user:
            size = item.get("size", 0)
            out.append({
                "type": "knowledge", 
                "id": item["id"], 
                "filename": item["filename"], 
                "uploaded_at": item["uploaded_at"], 
                "size_bytes": size, 
                "status": item.get("status")
            })
            total_bytes += size

    # Calculate legacy catalogs as well if they belong to this user (we migrated to "legacy" but this handles generic users)
    return {"files": out, "total_bytes": total_bytes, "quota_bytes": 500 * 1024 * 1024}

@router.delete("/api/upload/{filename}")
async def delete_catalog(filename: str, x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User")) -> dict[str, Any]:
    user = api_server._require_user(x_billszuka_user)
    clean = api_server._validate_filename(filename)
    
    with db.connect() as conn:
        row = conn.execute("SELECT filename FROM catalog_files WHERE filename=? AND uploaded_by=?", (clean, user)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="File not found or not owned by user")
        conn.execute("DELETE FROM catalog_files WHERE filename=?", (clean,))
    
    target = api_server.DATA / "users" / user / "catalogs" / clean
    if target.exists():
        target.unlink()
        
    return {"ok": True, "message": f"Deleted {clean}"}

@router.delete("/api/knowledge/{file_id}")
async def delete_knowledge(file_id: str, x_billszuka_user: str | None = Header(None, alias="X-Billszuka-User")) -> dict[str, Any]:
    user = api_server._require_user(x_billszuka_user)
    items = api_server._read_knowledge_index()
    target_item = None
    for item in items:
        if item["id"] == file_id:
            target_item = item
            break
            
    if not target_item or target_item.get("uploaded_by") != user:
        raise HTTPException(status_code=404, detail="Knowledge file not found or not owned by user")
    
    # Delete from Gemini
    api_key = api_server._get_first_gemini_key()
    if api_key and "gemini_name" in target_item:
        try:
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/{target_item['gemini_name']}?key={api_key}",
                method="DELETE"
            )
            def _del():
                try:
                    urllib.request.urlopen(req)
                except urllib.error.URLError:
                    pass
            await asyncio.to_thread(_del)
        except Exception:
            pass

    # Delete local
    local_path = api_server.ROOT / target_item["local_path"]
    if local_path.exists():
        local_path.unlink()
    
    # Update index
    new_items = [i for i in items if i["id"] != file_id]
    api_server._write_knowledge_index(new_items)
    
    return {"ok": True, "message": f"Deleted {target_item['filename']}"}
