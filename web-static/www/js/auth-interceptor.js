'use strict';
  
//
//  Adapted from:
//    https://github.com/danieljoos/aws-sign-web/blob/master/README.md
//

angular
.module('authInterceptor', ['webchatApiEndpoint'])
.factory('AwsAuthInterceptor', function ($q, $cookieStore, WebChatApiEndpoint) {
    
  var defaultAuthConfig = {};
  
  var noSignSuffixes = [".html", ".js", ".css", ".woff2"];
  
  /*
    endsWith function for string, in case browser doesn't have native method.
  */
  var endsWith = function(str, suffix) {
      return str.indexOf(suffix, str.length - suffix.length) !== -1;
  }
  
  /*
      Need to fetch API signature settings.
  
      Only explicitly necessary due to the AWS region string being required 
      for AWS v4 signatures.
  */
  var signatureConfigRequestPath = WebChatApiEndpoint + "api";
  
  var getSignatureConfigSettings = function() {
    return $q(function(resolve, reject) {
      
      if (defaultAuthConfig.hasOwnProperty("region") && defaultAuthConfig.hasOwnProperty("service")) {
        resolve(true);
      }
      
      var xmlHttp = new XMLHttpRequest();
      xmlHttp.addEventListener("loadend", function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
          var responseObject = JSON.parse(xmlHttp.responseText);
          
          defaultAuthConfig["region"] = responseObject["aws-v4-sig"]["region"]
          defaultAuthConfig["service"] = responseObject["aws-v4-sig"]["service"]
          
          resolve(true);
        }
        else {
          console.log(xmlHttp);
          reject("Other");
        }
      })
      
      xmlHttp.open("GET", signatureConfigRequestPath, true);
      xmlHttp.send();
    });
  }
  
  var signRequestWithConfig = function(config) {
    
    var retrievedCredentialSet = undefined;
    
    var userLoginObject = $cookieStore.get("login");
    if (!angular.isUndefined(userLoginObject)) {
      retrievedCredentialSet = userLoginObject.credentials;
    }

    if (angular.isUndefined(retrievedCredentialSet)) {
      //console.log("No existing credentials found. Not signing request.");
    }
    else {
      config.awsAuth = {
        accessKeyId: retrievedCredentialSet["access-key-id"],
        secretAccessKey: retrievedCredentialSet["secret-access-key"],
        sessionToken: retrievedCredentialSet["session-token"]
      }
    }
  
    if (angular.isUndefined(config.awsAuth) || !config.awsAuth) {
      return config;
    }
    var authConfig = angular.extend({}, defaultAuthConfig, config.awsAuth);
    delete config.awsAuth;

    if (angular.isUndefined(authConfig.accessKeyId) ||
      angular.isUndefined(authConfig.secretAccessKey)) {
      return config;
    }
    // Re-use existing request transformers for generating the payload.
    if (config.transformRequest) {
      authConfig.payloadSerializer = function() {
        return config.transformRequest.reduce(function(prev, transformer) {
          return transformer(prev);
        }, config.data);
      };
    }

    // Create the authentication headers and merge them into the existing ones
    var signer = new awsSignWeb.AwsSigner(authConfig);
    var signed = signer.sign(config);

    angular.merge(config.headers, signed);
    
    return config;
    
  }

  function onRequest(config) {
    
    var shouldSign = true;
    
    var deferred = $q.defer();
    
    for (var i = 0; i < noSignSuffixes.length; i++) {
      var eachSuffix = noSignSuffixes[i];
      if (endsWith(config.url, eachSuffix)) {
        shouldSign = false;
        break;
      }
    }
    
    var userLoginObject = $cookieStore.get("login");
    if (!angular.isUndefined(userLoginObject)) {
      if (userLoginObject.user.hasOwnProperty("api-key")) {
        var apiKey = userLoginObject.user["api-key"];
        config.headers["x-api-key"] = apiKey;
      }
    }
    
    if (shouldSign) {
      getSignatureConfigSettings()
        .then(function() {
          deferred.resolve(signRequestWithConfig(config));
        })
        .catch(function() {
          deferred.reject(...arguments);
        })
    }
    else {
      // This is just a request for static web resources. No need to sign.
      deferred.resolve(config);
    }
    
    return deferred.promise;
    
  }
  
  return {
      request: onRequest
  };
  
})
.config(function ($httpProvider) {
    $httpProvider.interceptors.push('AwsAuthInterceptor');
});