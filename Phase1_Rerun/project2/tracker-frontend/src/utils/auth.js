//The Web Storage API provides mechanisms by which browsers can securely store key/value pairs.
//The keys and the values are always strings
//  (note that, as with objects, integer keys will be automatically converted to strings)
//MANIPULATING the session storage for a domain - Window.sessionStorage(get cleared at the end of session)
//              the local storage - Window.localStorage (has no expiratiion time)
//Storage.length(Read Only) - return the no of data items stored in a given Storage object
//Storage.getItem() -When passed a key name, will return that key's value.

//Storage.setItem(keyName, keyValue)-When passed a key name and value, will add that key to the storage, 
// or update that key's value if it already exists.

//Storage.removeItem()-When passed a key name, will remove that key from the storage.

//Storage.clear() - When invoked, will empty all keys out of the storage.
//setStyles()  - grabs the data items using Storage.getItem()
//populateStorage(), which uses Storage.setItem() to set the item values, then runs setStyles().
//Storage only supports storing and retrieving strings. If you want to save other data types, you have to convert them to strings.
//  For plain objects and arrays, you can use JSON.stringify().


//Retrieves from local storage
export function isAuthenticated() {
    const token = getToken()
    if (token) {
        return true
    } else {
        return false
    }
}

//Save item
export function saveToken(token) {
    window.localStorage.setItem("token", token)
}
//Get item
export function getToken() {
    return window.localStorage.getItem("token")
}
//Removes item
export function removeToken() {
    window.localStorage.removeItem("token")
}