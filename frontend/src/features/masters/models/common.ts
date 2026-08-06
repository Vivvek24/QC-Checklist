/**
 * Shapes shared by every compliance master.
 *
 * The six masters form one hierarchy:
 *
 *     Country ─┬─ State ─── CategoryOfLaw
 *              └─ Legislation ─── Rule
 *
 *     TaskType (independent lookup)
 *
 * A nullable `state_id` on a child means country-wide (central), not "not set".
 */

/** Identity and audit columns every master carries, via the backend AuditMixin. */
export interface MasterRecord {
  id: string;
  is_active: boolean;
  created_by: string;
  created_date: string;
  modified_by: string;
  modified_date: string;
}

/** One page of a master list, normalised away from each endpoint's envelope key. */
export interface MasterPage<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

/** Filters every master list endpoint accepts. */
export interface MasterListParams {
  skip?: number;
  limit?: number;
  search?: string;
  is_active?: boolean;
}

/** A master that can be offered in a parent picker. */
export type LabelledMaster = MasterRecord & { code: string; name: string };
