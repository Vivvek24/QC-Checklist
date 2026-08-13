import type { MasterListParams, MasterRecord } from './common';

export interface Product extends MasterRecord {
  product_name: string;
  storage_conditions: string;
}

export interface CreateProductRequest {
  product_name: string;
  storage_conditions: string;
  is_active: boolean;
}

export type UpdateProductRequest = Partial<CreateProductRequest>;
export type ProductListParams = MasterListParams;
