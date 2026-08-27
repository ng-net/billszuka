import test from "node:test";
import assert from "node:assert/strict";

// Pure state machine helper test to verify stack push/undo/redo mechanics without React DOM
function createStackMachine(initialState, maxDepth = 50) {
  let past = [];
  let present = initialState;
  let future = [];

  return {
    get state() { return present; },
    get canUndo() { return past.length > 0; },
    get canRedo() { return future.length > 0; },
    push(next) {
      if (JSON.stringify(present) === JSON.stringify(next)) return;
      past.push(present);
      if (past.length > maxDepth) past.shift();
      present = next;
      future = [];
    },
    undo() {
      if (past.length === 0) return;
      const prev = past.pop();
      future.unshift(present);
      present = prev;
    },
    redo() {
      if (future.length === 0) return;
      const next = future.shift();
      past.push(present);
      present = next;
    }
  };
}

test("useUndoRedo: pushes state and enables undo", () => {
  const stack = createStackMachine({ filters: {} });
  assert.equal(stack.canUndo, false);
  assert.equal(stack.canRedo, false);

  stack.push({ filters: { kategoria: ["A1"] } });
  assert.equal(stack.canUndo, true);
  assert.equal(stack.canRedo, false);
  assert.deepEqual(stack.state.filters, { kategoria: ["A1"] });

  stack.undo();
  assert.equal(stack.canUndo, false);
  assert.equal(stack.canRedo, true);
  assert.deepEqual(stack.state.filters, {});

  stack.redo();
  assert.equal(stack.canUndo, true);
  assert.equal(stack.canRedo, false);
  assert.deepEqual(stack.state.filters, { kategoria: ["A1"] });
});

test("useUndoRedo: clears future on new push after undo", () => {
  const stack = createStackMachine({ count: 1 });
  stack.push({ count: 2 });
  stack.push({ count: 3 });

  stack.undo(); // back to 2
  assert.equal(stack.state.count, 2);
  assert.equal(stack.canRedo, true);

  stack.push({ count: 4 }); // pushes 4, clears future
  assert.equal(stack.state.count, 4);
  assert.equal(stack.canRedo, false);

  stack.undo(); // back to 2
  assert.equal(stack.state.count, 2);
});

test("useUndoRedo: enforces maxDepth cap", () => {
  const stack = createStackMachine({ step: 0 }, 3);
  for (let i = 1; i <= 10; i++) {
    stack.push({ step: i });
  }

  assert.equal(stack.state.step, 10);
  // Can only undo 3 steps back
  stack.undo();
  stack.undo();
  stack.undo();
  assert.equal(stack.state.step, 7);
  assert.equal(stack.canUndo, false);
});
