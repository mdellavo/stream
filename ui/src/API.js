import $ from 'jquery';

const API_ROOT = 'http://localhost:8080';

class _API {
    constructor(api_root) {
        this.api_root = api_root;
    }
    buildXHR(method, path, data, success, error) {
        return $.ajax({
            dataType: "json",
            method: method,
            url: this.api_root + path,
            headers: {
            },
            data: data,
            success: success,
            error: error
        });
    }
    buildXHRJson(method, path, data, success, error) {
        return this.buildXHR(method, path, JSON.stringify(data), success, error);
    }
    checkStatus(success, error) {
        return this.buildXHR("GET", "/", null, success, error);
    }
    getPlaylists(success, error) {
        return this.buildXHR("GET", "/playlists", null, success, error);
    }
}

const API = new _API(API_ROOT);

export default API;
