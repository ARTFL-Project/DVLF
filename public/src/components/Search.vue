<template>
    <div class="container-fluid">
        <div style="text-align: center; margin-top: 30px" v-if="atHome">
            <p class="lead">Découvrez...explorez...définissez...votre langue</p>
        </div>

        <div style="text-align: center" :class="{ 'mt-4': !atHome }">
            <img
                style="max-height: 150px; max-width: 100%; margin-bottom: 20px"
                alt="Brand"
                src="../assets/images/dvlf_logo_medium_no_beta_transparent.png"
                v-if="atHome"
            />
            <b-row>
                <b-col
                    sm="8"
                    offset-sm="2"
                    md="6"
                    offset-md="3"
                    offset-lg="3"
                    lg="6"
                    offset-xl="4"
                    xl="4"
                    align-self="center"
                >
                    <form @submit.prevent @keyup.enter="search()">
                        <b-input-group class="shadow-sm">
                            <b-form-input
                                id="search-input"
                                autocomplete="off"
                                :name="queryTerm"
                                placeholder="Tapez un mot..."
                                aria-describedby="search"
                                v-model="queryTerm"
                                @input="onChange"
                                @keyup.down.native="onArrowDown"
                                @keyup.up.native="onArrowUp"
                                @keyup.enter.native="onEnter"
                            ></b-form-input>
                            <b-input-group-append>
                                <b-btn variant="primary" @click="search">Rechercher</b-btn>
                            </b-input-group-append>
                        </b-input-group>
                        <ul id="autocomplete-results" class="shadow-sm" v-if="isOpen">
                            <li
                                tabIndex="-1"
                                v-for="(result, i) in autoCompleteResults"
                                :key="i"
                                @click="setResult(result.headword)"
                                class="autocomplete-result"
                                :class="{ 'is-active': i === arrowCounter }"
                                v-html="result.html"
                            ></li>
                        </ul>
                    </form>
                </b-col>
            </b-row>
        </div>
        <div style="text-align: center; margin-top: 10px" v-if="atHome">
            <h4>
                Notre mot du jour :
                <router-link :to="`/mot/${wordOfTheDay}`">{{ wordOfTheDay }}</router-link>
            </h4>
        </div>
    </div>
</template>
<script>
import { EventBus } from "../main.js";

export default {
    name: "Search",
    data: function () {
        return {
            atHome: true,
            queryTerm: "",
            typed: "",
            wordOfTheDay: "tradition",
            aPropos: false,
            isOpen: false,
            autoCompleteResults: [],
            isLoading: false,
            arrowCounter: 0,
        };
    },
    watch: {
        $route(to, from) {
            if (to.path === "/") {
                this.atHome = true;
            }
            this.queryTerm = "";
        },
    },
    created() {
        if (this.$route.path.slice(0, 4) == "/mot") {
            this.atHome = false;
        }
        let vm = this;
        EventBus.$on("OffHome", function () {
            vm.atHome = false;
        });
        this.$http(`${this.$globalConfig.apiServer}/api/wordoftheday`).then(function (response) {
            vm.wordOfTheDay = response.data;
        });
    },
    methods: {
        search() {
            this.$router.push(`/mot/${this.queryTerm}`);
            this.atHome = false;
            this.isOpen = false;
        },
        onChange() {
            // Let's warn the parent that a change was made
            this.isLoading = true;
            this.typed = this.queryTerm;
            if (this.typed.length > 1 && this.typed != this.$route.params.queryTerm) {
                var vm = this;
                this.$http
                    .get(`${this.$globalConfig.apiServer}/api/autocomplete/${this.typed}`)
                    .then(function (response) {
                        vm.autoCompleteResults = response.data;
                        vm.isOpen = true;
                        vm.isLoading = false;
                        vm.typed = "";
                    });
            }
        },
        setResult(result) {
            this.queryTerm = result;
            this.isOpen = false;
        },
        onArrowDown(evt) {
            if (this.arrowCounter < this.autoCompleteResults.length) {
                this.arrowCounter = this.arrowCounter + 1;
            }
            let container = document.getElementById("autocomplete-results");
            let topOffset = container.scrollTop;
            container.scrollTop = topOffset + 36;
        },
        onArrowUp() {
            if (this.arrowCounter > 0) {
                this.arrowCounter = this.arrowCounter - 1;
            }
            let container = document.getElementById("autocomplete-results");
            let topOffset = container.scrollTop;
            container.scrollTop = topOffset - 36;
        },
        onEnter() {
            this.queryTerm = this.autoCompleteResults[this.arrowCounter].headword.replace(/<[^>]+>/g, "");
            this.arrowCounter = -1;
            this.isOpen = false;
            this.autoCompleteResults = [];
        },
        handleClickOutside(evt) {
            if (!this.$el.contains(evt.target)) {
                this.isOpen = false;
                this.arrowCounter = -1;
            }
        },
    },
    mounted() {
        document.addEventListener("click", this.handleClickOutside);
    },
    destroyed() {
        document.removeEventListener("click", this.handleClickOutside);
    },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.container-fluid {
    font-size: 90%;
}

.form-control:focus {
    border-color: transparent !important;
}

.lead {
    margin-top: 15px;
}
#search-input {
    font-size: 1.2rem;
}
.autocomplete {
    position: relative;
}

#autocomplete-results {
    padding: 0;
    margin: 3px 0 0 15px;
    border: 1px solid #eeeeee;
    border-top-width: 0px;
    max-height: 216px;
    overflow-y: scroll;
    width: 267px;
    position: absolute;
    left: 0;
    background-color: #fff;
    z-index: 100;
    top: 34px;
    font-size: 1.2rem;
}

.autocomplete-result {
    list-style: none;
    text-align: left;
    padding: 4px 12px;
    cursor: pointer;
    font-size: 1.2rem;
}

.autocomplete-result:hover,
.is-active {
    background-color: #ddd;
    color: black;
}
</style>
