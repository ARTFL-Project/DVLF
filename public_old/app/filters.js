(function() {
    "use strict";

    angular
        .module("DVLF")
        .filter("isEmpty", isEmpty)
        .filter("unsafe", unSafe)
        .filter('encodeURIComponent', encode);


    function isEmpty() {
        return function(obj) {
            if (angular.element.isEmptyObject(obj)) {
                return false;
            } else {
                return true;
            }
        };
    }

    function unSafe($sce) {
        return $sce.trustAsHtml;
    }

    function encode($window) {
        return $window.encodeURIComponent;
    }
})();
