'use strict';

angular
.module('webchatApiEndpoint', [])
.factory('WebChatApiEndpoint', function () {
  
  var apiEndpoint = "";
  
  if (!angular.isUndefined(GlobalWebChatApiEndpoint)) {
    apiEndpoint = GlobalWebChatApiEndpoint;
  }
  
  return apiEndpoint;
})