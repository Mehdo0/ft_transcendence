export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set([]),
	mimeTypes: {},
	_: {
		client: {start:"_app/immutable/entry/start.BN7VN3Xo.js",app:"_app/immutable/entry/app.BBE7NACQ.js",imports:["_app/immutable/entry/start.BN7VN3Xo.js","_app/immutable/chunks/ClfMKyPi.js","_app/immutable/chunks/BZMfIxyW.js","_app/immutable/chunks/DRsxHkMd.js","_app/immutable/entry/app.BBE7NACQ.js","_app/immutable/chunks/BZMfIxyW.js","_app/immutable/chunks/C-_02kA4.js","_app/immutable/chunks/CK-Cv2UY.js","_app/immutable/chunks/DRsxHkMd.js","_app/immutable/chunks/CfpKsqlZ.js","_app/immutable/chunks/CbR6Gvdm.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
