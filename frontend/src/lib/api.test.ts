import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import type { AxiosInstance } from 'axios';
// @ts-expect-error - api.ts doesn't exist yet (TDD RED phase)
import { get, post, put, del } from './api';

// Mock axios
vi.mock('axios');

describe('API Client', () => {
    let mockAxiosInstance: Partial<AxiosInstance>;
    let mockGet: ReturnType<typeof vi.fn>;
    let mockPost: ReturnType<typeof vi.fn>;
    let mockPut: ReturnType<typeof vi.fn>;
    let mockDelete: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        // Setup mock axios instance methods
        mockGet = vi.fn();
        mockPost = vi.fn();
        mockPut = vi.fn();
        mockDelete = vi.fn();

        mockAxiosInstance = {
            get: mockGet,
            post: mockPost,
            put: mockPut,
            delete: mockDelete,
            interceptors: {
                request: {
                    use: vi.fn((onFulfilled) => {
                        // Store the request interceptor for testing
                        (mockAxiosInstance as any).requestInterceptor = onFulfilled;
                        return 0;
                    }),
                    eject: vi.fn(),
                },
                response: {
                    use: vi.fn((onFulfilled, onRejected) => {
                        // Store the response interceptors for testing
                        (mockAxiosInstance as any).responseInterceptor = onFulfilled;
                        (mockAxiosInstance as any).errorInterceptor = onRejected;
                        return 0;
                    }),
                    eject: vi.fn(),
                },
            } as any,
        };

        // Mock axios.create to return our mock instance
        vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as AxiosInstance);

        // Clear localStorage
        localStorage.clear();
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('HTTP Methods', () => {
        it('should make GET request and return data', async () => {
            const mockData = { id: 1, name: 'Test' };
            mockGet.mockResolvedValue({ data: mockData });

            const result = await get('/test');

            expect(mockGet).toHaveBeenCalledWith('/test', undefined);
            expect(result).toEqual(mockData);
        });

        it('should make GET request with config', async () => {
            const mockData = { id: 1, name: 'Test' };
            const config = { params: { page: 1 } };
            mockGet.mockResolvedValue({ data: mockData });

            const result = await get('/test', config);

            expect(mockGet).toHaveBeenCalledWith('/test', config);
            expect(result).toEqual(mockData);
        });

        it('should make POST request and return data', async () => {
            const requestData = { name: 'New Item' };
            const responseData = { id: 1, ...requestData };
            mockPost.mockResolvedValue({ data: responseData });

            const result = await post('/test', requestData);

            expect(mockPost).toHaveBeenCalledWith('/test', requestData, undefined);
            expect(result).toEqual(responseData);
        });

        it('should make POST request with config', async () => {
            const requestData = { name: 'New Item' };
            const responseData = { id: 1, ...requestData };
            const config = { headers: { 'X-Custom': 'value' } };
            mockPost.mockResolvedValue({ data: responseData });

            const result = await post('/test', requestData, config);

            expect(mockPost).toHaveBeenCalledWith('/test', requestData, config);
            expect(result).toEqual(responseData);
        });

        it('should make PUT request and return data', async () => {
            const requestData = { name: 'Updated Item' };
            const responseData = { id: 1, ...requestData };
            mockPut.mockResolvedValue({ data: responseData });

            const result = await put('/test/1', requestData);

            expect(mockPut).toHaveBeenCalledWith('/test/1', requestData, undefined);
            expect(result).toEqual(responseData);
        });

        it('should make DELETE request', async () => {
            mockDelete.mockResolvedValue({ data: undefined });

            const result = await del('/test/1');

            expect(mockDelete).toHaveBeenCalledWith('/test/1', undefined);
            expect(result).toBeUndefined();
        });
    });

    describe('Request Interceptor - Authentication', () => {
        it('should add Authorization header when token exists in localStorage', () => {
            // Set token in localStorage
            const mockToken = 'test-jwt-token';
            localStorage.setItem('auth_token', mockToken);

            // Re-import to trigger interceptor registration
            vi.resetModules();
            // This will re-run the module and register interceptors
            require('./api');

            // Get the registered request interceptor
            const requestInterceptor = (mockAxiosInstance as any).requestInterceptor;
            expect(requestInterceptor).toBeDefined();

            // Test the interceptor
            const config = { headers: {} };
            const modifiedConfig = requestInterceptor(config);

            expect(modifiedConfig.headers.Authorization).toBe(`Bearer ${mockToken}`);
        });

        it('should not add Authorization header when token does not exist', () => {
            // Ensure no token in localStorage
            localStorage.removeItem('auth_token');

            // Re-import to trigger interceptor registration
            vi.resetModules();
            require('./api');

            // Get the registered request interceptor
            const requestInterceptor = (mockAxiosInstance as any).requestInterceptor;
            expect(requestInterceptor).toBeDefined();

            // Test the interceptor
            const config = { headers: {} };
            const modifiedConfig = requestInterceptor(config);

            expect(modifiedConfig.headers.Authorization).toBeUndefined();
        });
    });

    describe('Response Interceptor - Error Handling', () => {
        it('should handle 401 Unauthorized error', async () => {
            const error = {
                response: {
                    status: 401,
                    data: { detail: 'Unauthorized' },
                },
                config: {},
                isAxiosError: true,
            };

            // Re-import to trigger interceptor registration
            vi.resetModules();
            require('./api');

            // Get the registered error interceptor
            const errorInterceptor = (mockAxiosInstance as any).errorInterceptor;
            expect(errorInterceptor).toBeDefined();

            // Test the interceptor
            await expect(errorInterceptor(error)).rejects.toMatchObject({
                response: {
                    status: 401,
                },
            });
        });

        it('should handle 403 Forbidden error', async () => {
            const error = {
                response: {
                    status: 403,
                    data: { detail: 'Forbidden' },
                },
                config: {},
                isAxiosError: true,
            };

            // Re-import to trigger interceptor registration
            vi.resetModules();
            require('./api');

            // Get the registered error interceptor
            const errorInterceptor = (mockAxiosInstance as any).errorInterceptor;
            expect(errorInterceptor).toBeDefined();

            // Test the interceptor
            await expect(errorInterceptor(error)).rejects.toMatchObject({
                response: {
                    status: 403,
                },
            });
        });

        it('should handle 404 Not Found error', async () => {
            const error = {
                response: {
                    status: 404,
                    data: { detail: 'Not Found' },
                },
                config: {},
                isAxiosError: true,
            };

            // Re-import to trigger interceptor registration
            vi.resetModules();
            require('./api');

            // Get the registered error interceptor
            const errorInterceptor = (mockAxiosInstance as any).errorInterceptor;
            expect(errorInterceptor).toBeDefined();

            // Test the interceptor
            await expect(errorInterceptor(error)).rejects.toMatchObject({
                response: {
                    status: 404,
                },
            });
        });

        it('should handle 422 Validation Error', async () => {
            const error = {
                response: {
                    status: 422,
                    data: {
                        detail: [
                            { loc: ['body', 'name'], msg: 'field required' },
                        ],
                    },
                },
                config: {},
                isAxiosError: true,
            };

            // Re-import to trigger interceptor registration
            vi.resetModules();
            require('./api');

            // Get the registered error interceptor
            const errorInterceptor = (mockAxiosInstance as any).errorInterceptor;
            expect(errorInterceptor).toBeDefined();

            // Test the interceptor
            await expect(errorInterceptor(error)).rejects.toMatchObject({
                response: {
                    status: 422,
                },
            });
        });

        it('should handle 500 Server Error', async () => {
            const error = {
                response: {
                    status: 500,
                    data: { detail: 'Internal Server Error' },
                },
                config: {},
                isAxiosError: true,
            };

            // Re-import to trigger interceptor registration
            vi.resetModules();
            require('./api');

            // Get the registered error interceptor
            const errorInterceptor = (mockAxiosInstance as any).errorInterceptor;
            expect(errorInterceptor).toBeDefined();

            // Test the interceptor
            await expect(errorInterceptor(error)).rejects.toMatchObject({
                response: {
                    status: 500,
                },
            });
        });

        it('should handle network error (no response)', async () => {
            const error = {
                message: 'Network Error',
                config: {},
                isAxiosError: true,
            };

            // Re-import to trigger interceptor registration
            vi.resetModules();
            require('./api');

            // Get the registered error interceptor
            const errorInterceptor = (mockAxiosInstance as any).errorInterceptor;
            expect(errorInterceptor).toBeDefined();

            // Test the interceptor
            await expect(errorInterceptor(error)).rejects.toMatchObject({
                message: 'Network Error',
            });
        });
    });
});
