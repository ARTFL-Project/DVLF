<template>
    <div id="app">
        <div id="overlay"></div>
        <Header />
        <b-container fluid>
            <Search />
            <router-view :key="$route.fullPath"></router-view>
        </b-container>
    </div>
</template>

<script>
import Header from "./components/Header.vue"
import Search from "./components/Search.vue"
import Results from "./components/Results.vue"

export default {
    name: "app",
    components: {
        Header,
        Search,
        Results
    }
}
</script>

<style>
body {
    counter-reset: section;
    /* Set the section counter to 0 */
    font-size: 95% !important;
    position: relative;
}
#overlay {
    position: absolute;
    height: 100%;
    width: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    display: none;
    z-index: 50;
}
/* Button colors */
.btn-primary {
    background-color: #fbfbfb !important;
    color: #333 !important;
    border-color: #ddd !important;
}

/* Links */
a {
    color: rgb(21, 95, 131) !important;
    font-weight: 400;
    transition: all 200ms;
}

a:hover {
    color: rgb(128, 0, 0) !important;
    text-decoration: none;
}

#waiting,
#waiting-inner,
#waiting-inner-inner {
    border-color: rgba(174, 89, 80, 0.5) rgba(143, 57, 49, 0.7)
        rgba(174, 89, 80, 0.5) rgba(174, 89, 80, 0.5);
}

.filter-list {
    color: rgb(109, 50, 39);
    font-weight: 400;
}

.navbar-right a:hover {
    color: #fff !important;
}

.btn-default {
    background-color: #fbfbfb;
}

.hidden {
    opacity: 0;
}
#app {
    color: rgb(61, 61, 61);
    margin: 0 auto;
    font-family: "Amiri", serif;
    font-weight: 300;
    position: relative;
}

.a-propos {
    text-align: justify;
}

a.btn:hover {
    color: #fff !important;
}

.hide-results {
    visibility: hidden;
}

.add-button {
    color: rgb(21, 95, 131);
    vertical-align: top;
}

.glyphicon.spinning {
    vertical-align: sub;
    animation: spin 1s infinite linear;
    -webkit-animation: spin2 1s infinite linear;
}

.nym-title,
.index,
#time-series-title {
    background-color: #f0f0f0;
    border-bottom: 1px solid #eee;
    text-align: center;
    margin-top: 0;
    padding: 7px;
    font-weight: 700;
}

.highlight {
    color: red;
}
.card-body {
    padding: 0 !important;
}

h3 {
    font-size: 1.35rem !important;
    margin-top: 0.3rem !important;
}
h4 {
    font-size: 1.1rem !important;
}

.submit-btn > .btn:first-of-type {
    background-color: rgba(21, 95, 131, 0.8) !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 150%;
    padding: 0.005rem 0.5rem;
}
textarea {
    width: 100%;
}
</style>
