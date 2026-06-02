//Axios Instance 
//Definition: An Axios instance is a separate Axios object with its own configuration.
//Created by: axios.create(config)
//Purpose: Avoids repeating request settings (like base URL, headers, or authentication tokens) across multiple calls.

import axios from "axios";
import { getToken, removeToken, saveToken } from "../utils/auth";
const VITE_API_URL = import.meta.env.VITE_API_URL;



const instance = axios.create({
    baseURL: VITE_API_URL,
    timeout: 10000,
    headers: { "Content-Type": "application/json" }
})

//Interceptors are powerful mechanism that can be used to intercept and modify HTTP requests and responses.
//Gets executed before a request is sent and before a response is received

instance.interceptors.request.use(
    function (config) {
        const token = getToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    function (error) {
        return Promise.reject(error);
    }
)

instance.interceptors.response.use(
    function (response) {
        return response
    },

    function (error) {
        console.error("Full error object:", error); // Log the entire error
        console.error("Error code:", error.code);   // Log the error code (e.g., 'ERR_NETWORK')
        console.error("Error message:", error.message);
        if (error.response?.status === 401 && !error.config.url.includes('/auth/login')) {
            removeToken()
            window.location.href = '/'
        }
        let message = "Network error: Unable to reach server"
        if (error.response) {
            message = error.response.data?.message || error.response.data?.error || error.message
        }
        return Promise.reject(new Error(message));
    }
)

export default instance;
