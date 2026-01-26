import { useDispatch, useSelector } from 'react-redux';
import type { TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './store';

export const useAppDispatch = () => useDispatch<AppDispatch>(); // Writing
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector; // Reading
