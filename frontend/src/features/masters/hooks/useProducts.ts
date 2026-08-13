import { productApi } from '../api/productApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type { Product, ProductListParams, CreateProductRequest, UpdateProductRequest } from '../models/Product';

const hooks = createMasterHooks<Product, CreateProductRequest, UpdateProductRequest, ProductListParams>(productApi, MASTER_KEYS.products);

export const useProducts = hooks.useList;
export const useCreateProduct = hooks.useCreate;
export const useUpdateProduct = hooks.useUpdate;
export const useDeleteProduct = hooks.useDelete;
