'use strict';
  
//
//  Adapted from:
//    https://github.com/danieljoos/aws-sign-web/blob/master/README.md
//

angular
.module('authInterceptor', [])
.factory('AwsAuthInterceptor', function ($cookieStore) {
    
  var apiSignatureSettings = WebChatApiSettings["aws-v4-sig"];
    
  var defaultAuthConfig = {
      region: apiSignatureSettings["region"],
      service: apiSignatureSettings["service"]
  };
  return {
      request: onRequest
  };


  function onRequest(config) {

    var retrievedCredentialSet = $cookieStore.get("credentials");

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
    
    if (!angular.isUndefined(retrievedCredentialSet)) {
      var apiKey = retrievedCredentialSet["api-key"];
      if (!angular.isUndefined(apiKey)) {
        config.headers["x-api-key"] = apiKey;
      }
    }

    return config;
  }
})
.config(function ($httpProvider) {
    $httpProvider.interceptors.push('AwsAuthInterceptor');
});