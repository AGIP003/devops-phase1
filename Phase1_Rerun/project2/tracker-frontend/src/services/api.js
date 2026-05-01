//Axios Instance 
//Definition: An Axios instance is a separate Axios object with its own configuration.
//Created by: axios.create(config)
//Purpose: Avoids repeating request settings (like base URL, headers, or authentication tokens) across multiple calls.

import axios from "axios";
import { getToken, saveToken } from "../utils/auth";
const VITE_API_URL = import.meta.env.VITE_API_URL;



const instance = axios.create({
    baseURL: VITE_API_URL,
    timeout: 10000,
    headers: { "Content-Type": "application/json header" }
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
        let message = "Network error: Unable to reach server"
        if (error.response) {
            message = error.response.data?.error || error.response.data?.message || error.message
        }
        return Promise.reject(new Error(message));
    }
)

export default instance;