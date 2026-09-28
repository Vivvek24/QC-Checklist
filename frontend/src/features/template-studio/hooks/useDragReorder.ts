/**
 * useDragReorder — generic native HTML5 drag-and-drop reordering for any list.
 * Shared within the template-studio feature — reused for reordering rows
 * (questions) in ConfigTable and sections in StageConfig.
 *
 * No external library. Wire the returned props onto each item's drag HANDLE
 * (not the whole row, so inputs/dropdowns inside the row stay clickable) and
 * onto the item's container for the drop target + hover indicator.
 *
 * Usage:
 *   const { getHandleProps, getItemProps, draggingIndex, dragOverIndex } =
 *     useDragReorder({ items: rows, onReorder: onRowsChange });
 *
 *   <tr {...getItemProps(index)}>
 *     <td><span {...getHandleProps(index)}><i className="pi pi-bars" /></span></td>
 *     ...
 *   </tr>
 */

import { useCallback, useState } from 'react';

export interface UseDragReorderOptions<T> {
  /** The current list, in display order. */
  items: T[];
  /** Called with the reordered list when a drop completes a move. */
  onReorder: (items: T[]) => void;
  /** Set false to temporarily disable dragging (e.g. while saving). Default true. */
  enabled?: boolean;
}

export interface UseDragReorderResult {
  /** Index currently being dragged, or null. */
  draggingIndex: number | null;
  /** Index currently hovered over as a drop target, or null. */
  dragOverIndex: number | null;
  /** Spread onto the small drag-handle element for item `index`. */
  getHandleProps: (index: number) => {
    draggable: true;
    onDragStart: (e: React.DragEvent) => void;
    onDragEnd: () => void;
    style: { cursor: string };
  };
  /** Spread onto the item's row/container element for item `index`. */
  getItemProps: (index: number) => {
    onDragOver: (e: React.DragEvent) => void;
    onDragLeave: () => void;
    onDrop: (e: React.DragEvent) => void;
  };
}

/**
 * Move the item at `from` to position `to`, returning a new array.
 * Exported for reuse anywhere a plain array move is needed without dragging.
 */
export const moveItem = <T,>(items: T[], from: number, to: number): T[] => {
  if (from === to || from < 0 || to < 0 || from >= items.length || to >= items.length) {
    return items;
  }
  const next = [...items];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved as T);
  return next;
};

export function useDragReorder<T>({
  items,
  onReorder,
  enabled = true,
}: UseDragReorderOptions<T>): UseDragReorderResult {
  const [draggingIndex, setDraggingIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  const getHandleProps = useCallback(
    (index: number) => ({
      draggable: true as const,
      onDragStart: (e: React.DragEvent) => {
        if (!enabled) return;
        setDraggingIndex(index);
        e.dataTransfer.effectAllowed = 'move';
        // Firefox requires setData to initiate a drag.
        e.dataTransfer.setData('text/plain', String(index));
      },
      onDragEnd: () => {
        setDraggingIndex(null);
        setDragOverIndex(null);
      },
      style: { cursor: enabled ? 'grab' : 'default' },
    }),
    [enabled]
  );

  const getItemProps = useCallback(
    (index: number) => ({
      onDragOver: (e: React.DragEvent) => {
        if (!enabled || draggingIndex === null) return;
        e.preventDefault(); // allow drop
        if (dragOverIndex !== index) setDragOverIndex(index);
      },
      onDragLeave: () => {
        setDragOverIndex((prev) => (prev === index ? null : prev));
      },
      onDrop: (e: React.DragEvent) => {
        if (!enabled || draggingIndex === null) return;
        e.preventDefault();
        onReorder(moveItem(items, draggingIndex, index));
        setDraggingIndex(null);
        setDragOverIndex(null);
      },
    }),
    [enabled, draggingIndex, dragOverIndex, items, onReorder]
  );

  return { draggingIndex, dragOverIndex, getHandleProps, getItemProps };
}
