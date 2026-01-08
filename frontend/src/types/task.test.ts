import { describe, it, expect } from 'vitest';
import type { Task, TaskStatus } from './task';
import { TaskStatus as TaskStatusEnum } from './task';

describe('Task Type Definitions', () => {
  describe('Task Interface', () => {
    it('should support started_at field (GREEN phase)', () => {
      // GREEN Phase: started_at field now exists in Task interface
      const mockTask: Task = {
        id: 1,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'pending',
        result: null,
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:00:00Z',
        started_at: '2026-01-08T10:00:00Z',
      };

      // Should PASS: started_at is now a valid optional field
      expect(mockTask.started_at).toBe('2026-01-08T10:00:00Z');
    });

    it('should support completed_at field (GREEN phase)', () => {
      // GREEN Phase: completed_at field now exists in Task interface
      const mockTask: Task = {
        id: 1,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'completed',
        result: '{"success": true}',
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:05:00Z',
        completed_at: '2026-01-08T10:05:00Z',
      };

      // Should PASS: completed_at is now a valid optional field
      expect(mockTask.completed_at).toBe('2026-01-08T10:05:00Z');
    });
  });

  describe('TaskStatus Enum', () => {
    it('should support CANCELLED status (GREEN phase)', () => {
      // GREEN Phase: CANCELLED status now exists in TaskStatus enum
      const cancelledStatus: TaskStatus = TaskStatusEnum.CANCELLED;

      // Should PASS: CANCELLED is now a valid status
      expect(cancelledStatus).toBe('cancelled');
    });

    it('should have CANCELLED status value equal to "cancelled"', () => {
      // GREEN Phase: Verify CANCELLED constant value
      const cancelledValue = TaskStatusEnum.CANCELLED;

      // Should PASS: CANCELLED value is 'cancelled'
      expect(cancelledValue).toBe('cancelled');
    });
  });
});
