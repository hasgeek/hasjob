importScripts('workbox-sw.prod.v2.1.2.js');

/**
 * DO NOT EDIT THE FILE MANIFEST ENTRY
 *
 * The method precache() does the following:
 * 1. Cache URLs in the manifest to a local cache.
 * 2. When a network request is made for any of these URLs the response
 *    will ALWAYS comes from the cache, NEVER the network.
 * 3. When the service worker changes ONLY assets with a revision change are
 *    updated, old cache entries are left as is.
 *
 * By changing the file manifest manually, your users may end up not receiving
 * new versions of files because the revision hasn't changed.
 *
 * Please use workbox-build or some other tool / approach to generate the file
 * manifest which accounts for changes to local files and update the revision
 * accordingly.
 */
const fileManifest = [
  {
    "url": "/static/build/css/stylesheet-app-css.5ef2418b8eca4bfba114.css",
    "revision": "9246f5c111548eefe1ad744355e54448"
  },
  {
    "url": "/static/build/css/stylesheet-vendor-css.5ef2418b8eca4bfba114.css",
    "revision": "ec2e4d901f3f8502fce1177a137cb736"
  },
  {
    "url": "/static/build/js/app-css.5ef2418b8eca4bfba114.js",
    "revision": "c91ca9c920681ae481725915a28330cc"
  },
  {
    "url": "/static/build/js/app.5ef2418b8eca4bfba114.js",
    "revision": "d21b1a5bbe4ec814d87d768b1f9fc8b5"
  },
  {
    "url": "/static/build/js/manifest.5ef2418b8eca4bfba114.js",
    "revision": "06f1ba3874e0e1c7087c774c396e150d"
  },
  {
    "url": "/static/build/js/vendor-css.5ef2418b8eca4bfba114.js",
    "revision": "dc8205d97322687041a432cabfc05acf"
  },
  {
    "url": "/static/build/js/vendor.5ef2418b8eca4bfba114.js",
    "revision": "12a1ca8d2cb2caab35d21438cb595e94"
  }
];

const workboxSW = new self.WorkboxSW({
  "cacheId": "hasjob",
  "skipWaiting": true,
  "clientsClaim": true
});
workboxSW.precache(fileManifest);
workboxSW.router.registerNavigationRoute("/");workboxSW.router.registerRoute(/^https?\:\/\/static.*/, workboxSW.strategies.networkFirst({
  "cacheName": "assets"
}), 'GET');
workboxSW.router.registerRoute(/^http:\/\/localhost:5000\/static/, workboxSW.strategies.networkFirst({
  "cacheName": "baseframe-local"
}), 'GET');
workboxSW.router.registerRoute(/^https?\:\/\/ajax.googleapis.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "cdn-libraries"
}), 'GET');
workboxSW.router.registerRoute(/^https?:\/\/cdnjs.cloudflare.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "cdn-libraries"
}), 'GET');
workboxSW.router.registerRoute(/^https?:\/\/images\.hasgeek\.com\/embed\/file\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "images"
}), 'GET');
workboxSW.router.registerRoute(/^https?:\/\/hasgeek.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "images"
}), 'GET');
workboxSW.router.registerRoute(/^https?:\/\/hasjob.co\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "images"
}), 'GET');
workboxSW.router.registerRoute(/^https?:\/\/fonts.googleapis.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "fonts"
}), 'GET');
workboxSW.router.registerRoute('/', workboxSW.strategies.networkFirst({
  "cacheName": "routes"
}), 'GET');
workboxSW.router.registerRoute('/*', workboxSW.strategies.networkFirst({
  "cacheName": "routes"
}), 'GET');
