//Axios Instance 
//Definition: An Axios instance is a separate Axios object with its own configuration.
//Created by: axios.create(config)
//Purpose: Avoids repeating request settings (like base URL, headers, or authentication tokens) across multiple calls.

import axios from "axios";
import.meta.env.VITE_API_URL



const instance = axios.create({
    baseURL: "https://api.example.com"
})