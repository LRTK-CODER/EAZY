import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock axios module with inline mock functions
vi.mock('axios', () => {
    const mockGet = vi.fn();
    const mockPost = vi.fn();
    const mockPut = vi.fn();
    const mockDelete = vi.fn();

    return {
        default: {
            create: vi.fn(() => ({
                get: mockGet,
                post: mockPost,
                put: mockPut,
                delete: mockDelete,
            })),
        },
        // Export mocks for test access
        __mockGet: mockGet,
        __mockPost: mockPost,
        __mockPut: mockPut,
        __mockDelete: mockDelete,
    };
});

import { get, post, put, del } from './api';
import axios from 'axios';

// Get mocked axios
const mockedAxios = vi.mocked(axios);
/* eslint-disable @typescript-eslint/no-explicit-any */
const mockAxiosInstance = (mockedAxios.create as any)() as any;

describe('API Client', () => {
    beforeEach(() => {
        // Clear all mocks before each test
        vi.clearAllMocks();
    });

    describe('HTTP Methods', () => {
        it('should make GET request and return data', async () => {
            const mockData = { id: 1, name: 'Test' };
            mockAxiosInstance.get.mockResolvedValue({ data: mockData });

            const result = await get('/test');

            expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', undefined);
            expect(result).toEqual(mockData);
        });

        it('should make GET request with params', async () => {
            const mockData = { id: 1, name: 'Test' };
            const params = { page: 1 };
            mockAxiosInstance.get.mockResolvedValue({ data: mockData });

            const result = await get('/test', params);

            expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', { params });
            expect(result).toEqual(mockData);
        });

        it('should make POST request and return data', async () => {
            const requestData = { name: 'New Item' };
            const responseData = { id: 1, ...requestData };
            mockAxiosInstance.post.mockResolvedValue({ data: responseData });

            const result = await post('/test', requestData);

            expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', requestData);
            expect(result).toEqual(responseData);
        });

        it('should make PUT request and return data', async () => {
            const requestData = { name: 'Updated Item' };
            const responseData = { id: 1, ...requestData };
            mockAxiosInstance.put.mockResolvedValue({ data: responseData });

            const result = await put('/test/1', requestData);

            expect(mockAxiosInstance.put).toHaveBeenCalledWith('/test/1', requestData);
            expect(result).toEqual(responseData);
        });

        it('should make DELETE request', async () => {
            mockAxiosInstance.delete.mockResolvedValue({ data: undefined });

            const result = await del('/test/1');

            expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test/1');
            expect(result).toBeUndefined();
        });
    });
});
