export type ResponseStateName = 'unassigned' | 'assigned' | 'investigating' | 'closed';
export type ResponseAction = 'acknowledge' | 'assign' | 'associate' | 'inspect' | 'act' | 'close' | 'reopen';
export interface ResponseState {
    revision: number;
    state: ResponseStateName;
    assignee_id: string | null;
    plant_id: number | null;
    station_code: string | null;
    updated_at: string | null;
}
export interface ResponseEvent {
    id: string;
    revision: number;
    actor_id: string;
    action: string;
    reason: string;
    details: Record<string, unknown>;
    created_at: string;
}
export interface OperationsReport {
    report: {
        id: string;
        category?: string;
        protocol_revision?: number;
        observation?: Record<string, unknown>;
        observed_at: string;
        created_at: string;
        latitude: number;
        longitude: number;
        note?: string | null;
        media_id?: string | null;
        condition?: string | null;
        reading_value?: number | null;
        reading_unit?: string | null;
        moderation_status: string;
        photo_source?: string | null;
        previous_observation_id?: string | null;
        level_change?: string | null;
    };
    response: ResponseState;
}
export interface OperationsDetail extends OperationsReport {
    events: ResponseEvent[];
}
export interface RegistryItem {
    id: string;
    label: string;
}
export function responseActions(state: ResponseStateName): ResponseAction[] { return state === 'closed' ? ['reopen'] : ['acknowledge', 'assign', 'associate', 'inspect', 'act', 'close']; }
export function responseEventBody(revision: number, action: ResponseAction, reason: string, fields: Record<string, unknown> = {}) { return { ...fields, expected_revision: revision, action, reason: reason.trim() }; }
export const actionLabels: Record<ResponseAction, string> = { acknowledge: 'Acknowledge', assign: 'Assign', associate: 'Link plant/station', inspect: 'Record inspection', act: 'Record action', close: 'Close case', reopen: 'Reopen case' };
export const stateLabels: Record<ResponseStateName, string> = { unassigned: 'Unassigned', assigned: 'Assigned', investigating: 'Investigating', closed: 'Closed' };
