import axios from "axios";

export const api = axios.create({
    baseURL: "http://localhost:8000/api/v1",
    headers: {
        "Content-Type": "application/json",
    },
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Handle global errors here (e.g., toast notifications)
        console.error("API Error:", error);
        return Promise.reject(error);
    }
);
