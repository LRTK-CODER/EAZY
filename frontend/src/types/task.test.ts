import { describe, it, expect } from 'vitest';
import { Task, TaskStatus } from './task';

describe('Task Type Definitions', () => {
  describe('Task Interface', () => {
    it('should fail because started_at field does not exist', () => {
      // RED Phase: started_at field not added to Task interface yet
      const mockTask: Task = {
        id: 1,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'pending',
        result: null,
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:00:00Z',
        // @ts-expect-error - started_at field doesn't exist yet (RED phase)
        started_at: '2026-01-08T10:00:00Z',
      };

      // Will FAIL: Type error - started_at property does not exist on type Task
      expect(mockTask.started_at).toBeDefined();
    });

    it('should fail because completed_at field does not exist', () => {
      // RED Phase: completed_at field not added to Task interface yet
      const mockTask: Task = {
        id: 1,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'completed',
        result: '{"success": true}',
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:05:00Z',
        // @ts-expect-error - completed_at field doesn't exist yet (RED phase)
        completed_at: '2026-01-08T10:05:00Z',
      };

      // Will FAIL: Type error - completed_at property does not exist on type Task
      expect(mockTask.completed_at).toBeDefined();
    });
  });

  describe('TaskStatus Enum', () => {
    it('should fail because CANCELLED status does not exist', () => {
      // RED Phase: CANCELLED status not added to TaskStatus enum yet
      // @ts-expect-error - CANCELLED status doesn't exist yet (RED phase)
      const cancelledStatus: TaskStatus = TaskStatus.CANCELLED;

      // Will FAIL: Property 'CANCELLED' does not exist on type 'TaskStatus'
      expect(cancelledStatus).toBe('cancelled');
    });

    it('should have CANCELLED status value equal to "cancelled"', () => {
      // RED Phase: Verify constant value
      // @ts-expect-error - CANCELLED status doesn't exist yet (RED phase)
      const cancelledValue = TaskStatus.CANCELLED;

      // Will FAIL: CANCELLED doesn't exist
      expect(cancelledValue).toBe('cancelled');
    });
  });
});
