/**
 * Permission Matrix Component
 * Component untuk menampilkan dan mengelola permission matrix dengan Tailwind CSS
 */

import React from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';
import type { LevelPermissionMatrixItem } from '../types';

export interface PermissionMatrixPermissions {
  can_read: boolean;
  can_create: boolean;
  can_update: boolean;
  can_delete: boolean;
}

interface PermissionMatrixProps {
  items: LevelPermissionMatrixItem[];
  saving?: boolean;
  onToggleAction: (menuId: number, action: keyof PermissionMatrixPermissions, value: boolean) => void;
  onToggleAll: (menuId: number, value: boolean) => void;
  onToggleSidebarVisibility?: (menuId: number, value: boolean) => void;
  onReorder?: (parentId: number | null, newOrder: LevelPermissionMatrixItem[]) => void;
  onReorderBoxes?: (newOrder: LevelPermissionMatrixItem[]) => void;
}

// Sortable Row Component
interface SortableRowProps {
  item: LevelPermissionMatrixItem;
  saving: boolean;
  onToggleAction: (menuId: number, action: keyof PermissionMatrixPermissions, value: boolean) => void;
  onToggleAll: (menuId: number, value: boolean) => void;
  onToggleSidebarVisibility?: (menuId: number, value: boolean) => void;
}

const SortableRow: React.FC<SortableRowProps> = ({
  item,
  saving,
  onToggleAction,
  onToggleAll,
  onToggleSidebarVisibility,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.menu_id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const allChecked = !!(
    item.permissions.can_read &&
    item.permissions.can_create &&
    item.permissions.can_update &&
    item.permissions.can_delete
  );

  return (
    <tr
      ref={setNodeRef}
      style={style}
      className={`hover:bg-gray-50 ${isDragging ? 'bg-gray-100' : ''}`}
    >
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center gap-2">
          <button
            {...attributes}
            {...listeners}
            className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 focus:outline-none"
            title="Drag untuk mengubah urutan"
          >
            <GripVertical className="w-5 h-5" />
          </button>
          <div>
            <div className="text-sm font-medium text-gray-900">{item.menu_name}</div>
            <div className="text-sm text-gray-500">{item.menu_path || item.menu_name}</div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-center">
        {onToggleSidebarVisibility ? (
          <input
            type="checkbox"
            checked={item.permissions.show_in_sidebar !== false}
            onChange={(e) => onToggleSidebarVisibility(item.menu_id, e.target.checked)}
            disabled={saving}
            className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            title="Tampilkan di sidebar"
          />
        ) : (
          <span className="text-gray-400">-</span>
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-center">
        <input
          type="checkbox"
          checked={allChecked}
          onChange={(e) => onToggleAll(item.menu_id, e.target.checked)}
          disabled={saving}
          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
      </td>
      {(['can_read', 'can_create', 'can_update', 'can_delete'] as const).map(action => (
        <td key={action} className="px-6 py-4 whitespace-nowrap text-center">
          <input
            type="checkbox"
            checked={item.permissions[action]}
            onChange={(e) => onToggleAction(item.menu_id, action, e.target.checked)}
            disabled={saving}
            className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
          />
        </td>
      ))}
    </tr>
  );
};

// Sortable Box Component (for reordering boxes)
interface SortableBoxProps {
  root: LevelPermissionMatrixItem;
  groupItems: LevelPermissionMatrixItem[];
  groupedByParent: Record<number, LevelPermissionMatrixItem[]>;
  saving: boolean;
  onToggleAction: (menuId: number, action: keyof PermissionMatrixPermissions, value: boolean) => void;
  onToggleAll: (menuId: number, value: boolean) => void;
  onToggleSidebarVisibility?: (menuId: number, value: boolean) => void;
  onReorder: (rootMenuId: number, newOrder: LevelPermissionMatrixItem[]) => void;
  sensors: ReturnType<typeof useSensors>;
}

const SortableBox: React.FC<SortableBoxProps> = ({
  root,
  groupItems,
  groupedByParent,
  saving,
  onToggleAction,
  onToggleAll,
  onToggleSidebarVisibility,
  onReorder,
  sensors,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: `box-${root.menu_id}` });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleDragEnd = (event: DragEndEvent, rootMenuId: number) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    // Get all items in this group (root + sub-menus)
    const items = [root, ...(groupedByParent[rootMenuId] || [])].filter(Boolean) as LevelPermissionMatrixItem[];

    const oldIndex = items.findIndex(item => item.menu_id === active.id);
    const newIndex = items.findIndex(item => item.menu_id === over.id);

    if (oldIndex !== -1 && newIndex !== -1) {
      const newOrder = arrayMove(items, oldIndex, newIndex);
      // Update order_index based on new position
      const updatedOrder = newOrder.map((item, index) => ({
        ...item,
        order_index: index + 1,
      }));

      if (onReorder) {
        onReorder(rootMenuId, updatedOrder);
      }
    }
  };

  const itemIds = groupItems.map(item => item.menu_id);

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white rounded-lg shadow-md overflow-hidden ${isDragging ? 'ring-2 ring-primary-500' : ''}`}
    >
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              {...attributes}
              {...listeners}
              className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 focus:outline-none"
              title="Drag untuk mengubah urutan box"
            >
              <GripVertical className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-semibold text-gray-900">{root.menu_name}</h3>
          </div>
          <span className="text-sm text-gray-500">
            {groupItems.length} permissions
          </span>
        </div>
      </div>
      <div className="overflow-x-auto" onPointerDown={(e) => e.stopPropagation()}>
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={(e) => {
            // Only handle row drags (not box drags)
            if (!String(e.active.id).startsWith('box-')) {
              handleDragEnd(e, root.menu_id);
            }
          }}
        >
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                  {/* Drag handle column */}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Permission
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Show in Sidebar
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  All
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  View
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Create
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Update
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Delete
                </th>
              </tr>
            </thead>
            <SortableContext items={itemIds} strategy={verticalListSortingStrategy}>
              <tbody className="bg-white divide-y divide-gray-200">
                {groupItems.map(item => (
                  <SortableRow
                    key={item.menu_id}
                    item={item}
                    saving={saving}
                    onToggleAction={onToggleAction}
                    onToggleAll={onToggleAll}
                    onToggleSidebarVisibility={onToggleSidebarVisibility}
                  />
                ))}
              </tbody>
            </SortableContext>
          </table>
        </DndContext>
      </div>
    </div>
  );
};

const PermissionMatrix: React.FC<PermissionMatrixProps> = ({
  items,
  saving = false,
  onToggleAction,
  onToggleAll,
  onToggleSidebarVisibility,
  onReorder,
  onReorderBoxes,
}) => {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const groupedByParent: Record<number, LevelPermissionMatrixItem[]> = items
    .slice()
    .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
    .reduce((acc, item) => {
      const pid = item.parent_id || 0;
      (acc[pid] = acc[pid] || []).push(item);
      return acc;
    }, {} as Record<number, LevelPermissionMatrixItem[]>);

  const rootMenus = groupedByParent[0] || [];
  const rootMenuIds = rootMenus.map(root => `box-${root.menu_id}`);

  const handleBoxDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    // Only handle box drags (check if ID starts with 'box-')
    if (!String(active.id).startsWith('box-') || !String(over.id).startsWith('box-')) {
      return;
    }

    const oldIndex = rootMenus.findIndex(root => `box-${root.menu_id}` === active.id);
    const newIndex = rootMenus.findIndex(root => `box-${root.menu_id}` === over.id);

    if (oldIndex !== -1 && newIndex !== -1) {
      const newOrder = arrayMove(rootMenus, oldIndex, newIndex);
      // Update order_index based on new position (multiply by 10 to leave room for sub-menus)
      const updatedOrder = newOrder.map((item, index) => ({
        ...item,
        order_index: (index + 1) * 10,
      }));

      if (onReorderBoxes) {
        onReorderBoxes(updatedOrder);
      }
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleBoxDragEnd}
    >
      <SortableContext items={rootMenuIds} strategy={verticalListSortingStrategy}>
        <div className="space-y-6">
          {rootMenus.map(root => {
            const groupItems = [root, ...(groupedByParent[root.menu_id] || [])];

            return (
              <SortableBox
                key={root.menu_id}
                root={root}
                groupItems={groupItems}
                groupedByParent={groupedByParent}
                saving={saving}
                onToggleAction={onToggleAction}
                onToggleAll={onToggleAll}
                onToggleSidebarVisibility={onToggleSidebarVisibility}
                onReorder={onReorder || (() => {})}
                sensors={sensors}
              />
            );
          })}
        </div>
      </SortableContext>
    </DndContext>
  );
};

export default PermissionMatrix;

