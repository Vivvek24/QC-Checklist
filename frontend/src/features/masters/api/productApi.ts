import { createMasterApi } from './createMasterApi';
import type { Product, ProductListParams, CreateProductRequest, UpdateProductRequest } from '../models/Product';

export const productApi = createMasterApi<Product, CreateProductRequest, UpdateProductRequest, ProductListParams>(
  '/masters/products', 'items'
);
