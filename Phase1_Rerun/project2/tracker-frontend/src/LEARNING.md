-> Every API has exactly 3 possible outcomes. UI must handle all 3
            loading: true   → show a spinner
                ↓
            error: "msg"    → show an error alert with retry button  
                ↓
            data: [...]     → show the table


            Component mounts
                  ↓
            loading = true → show spinner
                  ↓
            API call fires (useEffect)
                  ↓
            Success → loading = false, data = [...] → show table
            Failure → loading = false, error = "msg" → show error
//DECODING PAYLOAD(BASE64 ENCODED) IN JS.
const token = getToken()
const payload = JSON.parse(atob(token.split('.')[1]))
// payload.username, payload.email, payload.role - all there
//atob() - built in function that decodes base64
//split('.')[1] grabs the middle section - the payload



App owns: isLoggedIn state
    ↓ passes: onLoginSuccess function as prop
LoginForm calls: onLoginSuccess() after saving token
    ↓
App re-renders → isLoggedIn is now true → shows Dashboard