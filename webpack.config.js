var webpack = require('webpack');
var path = require("path");

var lib_dir = __dirname + '/hasjob/static/libs';

var config = {

  resolve: {
    alias: {
      react: lib_dir + '/react.js',
      reactDom: lib_dir + '/react-dom',
      jquery: lib_dir + '/jquery-1.11.3.min.js',
      jqueryAppear: lib_dir + '/jquery.appear.js'
    }
  },

  plugins: [
    new webpack.optimize.CommonsChunkPlugin('vendors', 'vendors.js', Infinity),
  ],

  entry: {
    hasjob: './hasjob/static/js/main.js',
    vendors: ['react', 'reactDom', 'jquery', 'jqueryAppear']
  },

  output: {
    path: path.join(__dirname, "hasjob/static/js"),
    filename: "[name].bundle.js"
  },

  module: {
    noParse: [
      new RegExp(lib_dir + './hasjob/static/libs/react-with-addons.js')
    ],
    loaders: [{
      test: /\.js$/,
      loader: 'jsx-loader'
    }]
  }
};

module.exports = config;
