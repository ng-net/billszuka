import { useState, useCallback, useRef } from "react";

/**
 * Custom hook to manage state with Undo / Redo history stack.
 *
 * @param {Object} initialState Initial state snapshot
 * @param {number} maxDepth Maximum history depth (default 50)
 */
export function useUndoRedo(initialState, maxDepth = 50) {
  const [past, setPast] = useState([]);
  const [present, setPresent] = useState(initialState);
  const [future, setFuture] = useState([]);

  // Debounce ref to group rapid consecutive calls (e.g. typing in search)
  const debounceTimerRef = useRef(null);
  const pendingStateRef = useRef(null);

  const canUndo = past.length > 0;
  const canRedo = future.length > 0;

  const undo = useCallback(() => {
    setPast((prevPast) => {
      if (prevPast.length === 0) return prevPast;
      const previous = prevPast[prevPast.length - 1];
      const newPast = prevPast.slice(0, prevPast.length - 1);

      setPresent((currentPresent) => {
        setFuture((prevFuture) => [currentPresent, ...prevFuture]);
        return previous;
      });

      return newPast;
    });
  }, []);

  const redo = useCallback(() => {
    setFuture((prevFuture) => {
      if (prevFuture.length === 0) return prevFuture;
      const next = prevFuture[0];
      const newFuture = prevFuture.slice(1);

      setPresent((currentPresent) => {
        setPast((prevPast) => [...prevPast, currentPresent]);
        return next;
      });

      return newFuture;
    });
  }, []);

  const pushState = useCallback(
    (newState, debounceMs = 0) => {
      if (debounceMs > 0) {
        pendingStateRef.current = newState;
        if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

        debounceTimerRef.current = setTimeout(() => {
          if (pendingStateRef.current !== null) {
            const next = pendingStateRef.current;
            pendingStateRef.current = null;

            setPresent((currentPresent) => {
              // Ignore if deep equal or identical
              if (JSON.stringify(currentPresent) === JSON.stringify(next)) {
                return currentPresent;
              }
              setPast((prevPast) => [...prevPast.slice(-maxDepth + 1), currentPresent]);
              setFuture([]);
              return next;
            });
          }
        }, debounceMs);
      } else {
        if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
        pendingStateRef.current = null;

        setPresent((currentPresent) => {
          if (JSON.stringify(currentPresent) === JSON.stringify(newState)) {
            return currentPresent;
          }
          setPast((prevPast) => [...prevPast.slice(-maxDepth + 1), currentPresent]);
          setFuture([]);
          return newState;
        });
      }
    },
    [maxDepth]
  );

  const reset = useCallback((newInitialState) => {
    setPast([]);
    setPresent(newInitialState);
    setFuture([]);
  }, []);

  return {
    state: present,
    set: pushState,
    undo,
    redo,
    reset,
    canUndo,
    canRedo,
    historyLength: past.length,
  };
}
