var webpack = require('webpack');
var path = require('path');
var dev = process.env.NODE_ENV === "development";
var extractTextPlugin = require('extract-text-webpack-plugin');
var cleanWebpackPlugin = require('clean-webpack-plugin');
var workboxPlugin = require('workbox-webpack-plugin');

function ManifestPlugin(options){
  this.manifestPath = options.manifestPath ? options.manifestPath : 'build/manifest.json';
}

ManifestPlugin.prototype.apply = function(compiler) {
  compiler.plugin('done', stats => {
    var stats_json = stats.toJson();
    var parsed_stats = {
      assets: stats_json.assetsByChunkName,
    }
    Object.keys(parsed_stats.assets).forEach(function(key) {
      if(typeof(parsed_stats.assets[key]) == "object") {
        for(var index in parsed_stats.assets[key]) {
          if(parsed_stats.assets[key][index].indexOf('.js') === -1 && 
            parsed_stats.assets[key][index].indexOf('stylesheet') > -1) {
            parsed_stats.assets[key] = parsed_stats.assets[key][index];
          }
        }
      }
    });
    require('fs').writeFileSync(
      path.join(__dirname, this.manifestPath),
      JSON.stringify(parsed_stats)
    );
  });
}

module.exports = {
  context: __dirname,
  devtool: dev ? "inline-sourcemap" : false,
  watch: dev ? true : false,
  resolve: {
    modules: [
      __dirname + '/node_modules'
    ]
  },
  entry: {
    "app": "./js/app.js",
    "vendor-css": "./sass/vendor.sass",
    "app-css": "./sass/app.sass",
  },
  output: {
    path: __dirname + "/build",
    publicPath: "/static/build/",
    filename: dev ? "js/[name].js" : "js/[name].[hash].js"
  },
  module: {
    loaders: [
    {
      test: /\.js$/,
      loader: 'babel-loader',
      query: {
        presets: [
          'babel-preset-es2015',
        ].map(require.resolve),
      }
    },
    {
      test: /\.css$/,
      loader: extractTextPlugin.extract({use: ['css-loader']}),
    },
    {
      test: /\.(sass|scss)$/,
      loader: extractTextPlugin.extract({ fallback: 'style-loader',  use:['css-loader','sass-loader'] }),
    },
    {
      test: /\.(png|jpe?g|gif|svg|woff|woff2|ttf|eot|ico)$/,
      loader: 'file-loader?name=assets/[name].[hash].[ext]'
    }]
  },
  plugins: dev ? [new ManifestPlugin({manifestPath: ''})] : [
    new cleanWebpackPlugin(['build']),
    new extractTextPlugin('css/stylesheet-[name].[hash].css'), //is used for generating css file bundles
    new ManifestPlugin({manifestPath: ''}),
    new webpack.optimize.UglifyJsPlugin({ mangle: false, sourcemap: true }),
    // keep module.id stable when vender modules does not change
    new webpack.HashedModuleIdsPlugin(),
    // split vendor js into its own file
    new webpack.optimize.CommonsChunkPlugin({
      name: 'vendor',
      minChunks: function (module) {
        // any required modules inside node_modules are extracted to vendor
        return (
          module.resource &&
          /\.js$/.test(module.resource) &&
          module.resource.indexOf(
            path.join(__dirname, '/node_modules')
          ) === 0
        )
      }
    }),
    // extract webpack runtime and module manifest to its own file in order to
    // prevent vendor hash from being updated whenever app bundle is updated
    new webpack.optimize.CommonsChunkPlugin({
      name: 'manifest',
      chunks: ['vendor']
    }),
    new workboxPlugin({
      cacheId: 'hasjob',
      globDirectory: './build/',
      globPatterns: ['**/*.{js,css}'],
      globIgnores: ['**/styles-*.{js}', '**/service-worker.js', '**/manifest.json'],
      swDest: './service-worker.js',
      clientsClaim: true,
      skipWaiting: true,
      navigateFallback: '/',
      runtimeCaching: [
        {
          urlPattern: /^https?\:\/\/static.*/,
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'assets'
            },
          },
        },
        {
          urlPattern: /^http:\/\/localhost:5000\/static/,
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'baseframe-local'
            },
          },
        },
        {
          urlPattern: /^https?\:\/\/ajax.googleapis.com\/*/,
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'cdn-libraries'
            },
          },
        },
        {
          urlPattern: /^https?:\/\/cdnjs.cloudflare.com\/*/,
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'cdn-libraries'
            },
          },
        },
        {
          urlPattern: /^https?:\/\/images\.hasgeek\.com\/embed\/file\/*/,
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'images'
            },
          },
        },
        {
          urlPattern: /^https?:\/\/hasgeek.com\/*/,
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'images'
            },
          },
        },
        {
          urlPattern: /^https?:\/\/hasjob.co\/*/,
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'images'
            },
          },
        },
        {
          urlPattern: /^https?:\/\/fonts.googleapis.com\/*/,
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'fonts'
            },
          },
        },
        {
          urlPattern: '/',
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'routes'
            },
          },
        },
        {
          urlPattern: '/*',
          handler: 'networkFirst',
          options: {
            cache: {
              name: 'routes'
            },
          },
        },
      ]
    })
  ],
};
