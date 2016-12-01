'use strict';

app.controller('modalSimpleController', function($scope, $state, $uibModalInstance) {
  
  $scope.goToLoginFormSubmitted = function() {
    $uibModalInstance.close();
    $state.go('login');
  };
  
});