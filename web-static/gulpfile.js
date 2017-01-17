var gulp = require('gulp');
var concat = require('gulp-concat');
var uglify = require('gulp-uglifyjs');
var less = require('gulp-less');
var minifyCss = require('gulp-minify-css');
var rename = require('gulp-rename');
var server = require('gulp-server-livereload');
var install = require("gulp-install");
var run = require('gulp-run');
var templateCache = require('gulp-angular-templatecache');
var dom = require('gulp-dom');
const del = require('del');

var devServerHost = 'localhost';

var config = {
  bowerDir: './bower_components'
}

gulp.task( 'server', ['build'], function() {
  gulp.src('./www')
    .pipe(server({
      livereload: true,
      clientConsole: false,
      directoryListing: false,
      open: false,
      host: devServerHost,
      port: 3000
    }));
});

gulp.task('icons', function() {
    return gulp.src(config.bowerDir + '/font-awesome/**/*')
      .pipe(gulp.dest('./www/lib/font-awesome/'));
});

gulp.task('ie10-viewport-bug-workaround', function() {
    return gulp.src(config.bowerDir + '/ie10-viewport-bug-workaround/dist/*')
      .pipe(gulp.dest('./www/lib/ie10-viewport-bug-workaround/'));
});

gulp.task('less', [], function(done) {
  gulp.src('./less/style.less')
    .pipe(less())
    .on('error', function(error) {
      console.error(error.toString());
      this.emit('end');
    })
    .pipe(gulp.dest('./www/css/'))
    .pipe(minifyCss({
      keepSpecialComments: 0
    }))
    .pipe(rename({ extname: '.min.css' }))
    .pipe(gulp.dest('./www/css/'))
    .on('end', done);
});

gulp.task('watch', function() {
  gulp.watch('./less/**/*.less', ['less']);
});

gulp.task('bootstrap', [], function(done) {
  var ends = 5;
  function end() {
    if (--ends) return;
    done();
  }
  gulp.src(['./node_modules/bootstrap/dist/**/', '!./**/npm.js'], {base: './node_modules/bootstrap/dist'})
    .pipe(gulp.dest('./www/lib/bootstrap/'))
    .on('end', end);
  gulp.src(['./node_modules/bootstrap/docs/assets/js/ie10-viewport-bug-workaround.js'], {base: './node_modules/bootstrap/docs/assets'})
    .pipe(gulp.dest('./www/lib/assets/'))
    .on('end', end);
  gulp.src(['./node_modules/html5shiv/dist/**/*'])
    .pipe(gulp.dest('./www/lib/html5shiv/'))
    .on('end', end);
  gulp.src(['./node_modules/Respond.js/dest/**/*'])
    .pipe(gulp.dest('./www/lib/respond/'))
    .on('end', end);
  gulp.src(['./node_modules/jquery/dist/*', '!./**/cdn'])
    .pipe(gulp.dest('./www/lib/jquery/'))
    .on('end', end);
});

gulp.task('angular-ui-bootstrap-install', function(done) {
  return gulp.src(['./node_modules/angular-ui-bootstrap/package.json'])
    .pipe(gulp.dest('./node_modules/angular-ui-bootstrap'))
    .pipe(install())

});

gulp.task('angular-ui-bootstrap-grunt', ['angular-ui-bootstrap-install'], function(done) {
  run('grunt --base ./node_modules/angular-ui-bootstrap --gruntfile ./node_modules/angular-ui-bootstrap/gruntfile.js html2js build')
    .exec('', function() {
      done();
    });
})

gulp.task('angular', [], function(done) {
  var ends = 6;
  function end() {
    if (--ends) return;
    done();
  }
  gulp.src(['./node_modules/angular/angular.js', './node_modules/angular/**/angular.min.js'])
    .pipe(gulp.dest('./www/lib/angular/js/'))
    .on('end', end);
  gulp.src(['./node_modules/angular-ui-router/release/**/*'])
    .pipe(gulp.dest('./www/lib/angular/js/'))
    .on('end', end);
  gulp.src(['./node_modules/angular/angular-csp.css'])
    .pipe(gulp.dest('./www/lib/angular/css/'))
    .on('end', end);
  gulp.src(['./node_modules//angular-animate/angular-animate.*'])
    .pipe(gulp.dest('./www/lib/angular/js/'))
    .on('end', end);
});

gulp.task('angular-cookies', function() {
    return gulp.src(config.bowerDir + '/angular-cookies/angular-cookies*.js')
      .pipe(gulp.dest('./www/lib/angular-cookies/'));
});

gulp.task('moment', function() {
    return gulp.src(config.bowerDir + '/moment/min/moment-with-locales*.js')
      .pipe(gulp.dest('./www/lib/moment/'));
});

gulp.task('spin-js', function() {
    return gulp.src(config.bowerDir + '/spin.js/spin*.js')
      .pipe(gulp.dest('./www/lib/spin-js/'));
});

gulp.task('crypto-js', function() {
    return gulp.src(config.bowerDir + '/crypto-js/*.js')
      .pipe(gulp.dest('./www/lib/crypto-js/'));
});

gulp.task('lato-font-css', function() {
    return gulp.src(config.bowerDir + '/lato-font/css/*.css')
      .pipe(gulp.dest('./www/lib/lato-font/css/'));
});

gulp.task('lato-font-fonts', function() {
    return gulp.src(config.bowerDir + '/lato-font/fonts/**/*')
      .pipe(gulp.dest('./www/lib/lato-font/fonts/'));
});

gulp.task('aws-sign-web', function() {
    return gulp.src(config.bowerDir + '/aws-sign-web/aws-sign-web*.js')
      .pipe(gulp.dest('./www/lib/aws-sign-web/'));
});

gulp.task('angular-ui-bootstrap', function() {
    return gulp.src('./node_modules/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js')
      .pipe(gulp.dest('./www/lib/angular/js/'));
});

gulp.task('template-cache', function () {
  return gulp.src('./templates/*.html')
    .pipe(templateCache())
    .pipe(gulp.dest('./www/lib/template-cache/'));
});

gulp.task('guid', function () {
  return gulp.src('./node_modules/guid/guid.js')
    .pipe(gulp.dest('./www/lib/guid/'));
});

gulp.task('error-html', function() {
  del('./www/error.html');
  
  return gulp.src('./www/index.html')
    .pipe(dom(function() {
      this.querySelectorAll('head')[0].innerHTML += '<script>var PageLoadErrorOccurred = true;</script>';
      return this;
    }))
    .pipe(rename({
      basename: "error",
      extname: ".html"
    }))
    .pipe(gulp.dest('./www/'))
})

gulp.task(
  'install', 
  [
    'build', 
    'icons', 
    'angular', 
    'bootstrap', 
    'angular-ui-bootstrap', 
    'ie10-viewport-bug-workaround', 
    'angular-cookies', 
    'crypto-js', 
    'aws-sign-web', 
    'moment',
    'spin-js',
    'lato-font-css',
    'lato-font-fonts',
    'template-cache',
    'guid',
    'error-html'
  ], 
  function(done) {
    done()
  }
);

gulp.task('build', ['less'], function(done) {
  done()
});

gulp.task('default', ['watch', 'server']);
