<template>
    <div style="padding: 10px; margin-top: 15px">
        <b-row>
            <b-col sm="12" md="8" lg="6" xl="7" offset-lg="2" order-sm="2" order-md="1">
                <transition name="fade">
                    <h3
                        :class="{ 'hide-results': apropos }"
                        style="text-align: center; animation-duration: 0.4s"
                        v-show="!loading"
                    >
                        <b>{{ currentTerm }}</b
                        >:
                        <span class="entry-total" v-show="totalResults > 0">
                            {{ totalResults }} {{ pluralize("entrée", totalResults) }} dans {{ totalDicos }}
                            {{ pluralize("dictionnaire", totalDicos) }}
                        </span>
                    </h3>
                </transition>
            </b-col>
            <b-col sm="12" md="4" xl="3" order-sm="1" order-md="2">
                <div class="float-right d-none d-md-inline shadow-sm">
                    <b-button-group class="submit-btn" size="sm">
                        <b-button variant="primary">+</b-button>
                        <b-dropdown id="second-btn" variant="primary" right text="Contribuer au DVLF">
                            <b-dropdown-item>
                                <router-link :to="`/definition/${currentTerm}`">Ajouter une définition</router-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <router-link :to="`/exemple/${currentTerm}`">Ajouter un exemple</router-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <router-link :to="`/synonyme/${currentTerm}`">Ajouter un synonyme</router-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <router-link :to="`/antonyme/${currentTerm}`">Ajouter un antonyme</router-link>
                            </b-dropdown-item>
                        </b-dropdown>
                    </b-button-group>
                </div>
                <div class="d-none d-sm-inline-block d-md-none mb-3" style="text-align: center; width: 100%">
                    <b-button-group class="submit-btn shadow-sm" size="sm">
                        <b-button variant="primary">+</b-button>
                        <b-dropdown id="second-btn" variant="primary" right text="Contribuer au DVLF">
                            <b-dropdown-item>
                                <router-link to="/definition">Ajouter une définition</router-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <router-link to="/exemple">Ajouter un exemple</router-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <router-link to="/synonyme">Ajouter un synonyme</router-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <router-link to="/antonyme">Ajouter un antonyme</router-link>
                            </b-dropdown-item>
                        </b-dropdown>
                    </b-button-group>
                </div>
            </b-col>
        </b-row>
        <b-row id="results">
            <b-col md="2" class="d-none d-lg-block" style="margin-top: 15px">
                <transition name="fade">
                    <word-wheel :headword="currentTerm" v-if="!loading" style="animation-duration: 0.4s"></word-wheel>
                </transition>
            </b-col>
            <b-col sm="12" md="8" lg="6" xl="7" v-if="!loading">
                <dictionary-entries
                    :results="results.dictionaries"
                    :fuzzy-results="results.fuzzyResults"
                ></dictionary-entries>
                <examples class="d-none d-md-block" :examples="results.examples"></examples>
            </b-col>
            <transition name="fade">
                <b-col class="mt-3" sm="12" md="4" xl="3" v-if="!loading">
                    <syn-anto-nyms :synonyms="results.synonyms" :antonyms="results.antonyms"></syn-anto-nyms>
                    <nearest-neighbors
                        :nearest-neighbors="results.nearestNeighbors"
                        :headword="currentTerm"
                        v-if="results.nearestNeighbors"
                    ></nearest-neighbors>
                    <collocations :collocates="results.collocates" :headword="currentTerm"></collocations>
                    <time-series :time-series="results.timeSeries" :headword="currentTerm"></time-series>
                </b-col>
            </transition>
            <transition name="fade">
                <b-col class="d-md-none" sm="12" v-if="!loading">
                    <examples :examples="results.examples"></examples>
                </b-col>
            </transition>
            <transition name="fade">
                <word-explorer :vectors="vectors" :headword="currentTerm" v-if="vectors"></word-explorer>
            </transition>
        </b-row>
    </div>
</template>

<script>
import DictionaryEntries from "./DictionaryEntries.vue";
import SynAntoNyms from "./SynAntoNyms.vue";
import Collocations from "./Collocations.vue";
import NearestNeighbors from "./NearestNeighbors.vue";
import TimeSeries from "./TimeSeries.vue";
import Examples from "./Examples.vue";
import WordWheel from "./WordWheel.vue";
import WordExplorer from "./WordExplorer.vue";
import { EventBus } from "../main.js";
require("vue2-animate/dist/vue2-animate.min.css");

export default {
    name: "Results",
    components: {
        DictionaryEntries,
        SynAntoNyms,
        Collocations,
        NearestNeighbors,
        TimeSeries,
        Examples,
        WordWheel,
        WordExplorer,
    },
    data: function () {
        return {
            currentTerm: this.$route.params.queryTerm,
            results: {},
            totalResults: 0,
            totalDicos: 0,
            atHome: true,
            apropos: false,
            loading: true,
            vectors: null,
        };
    },
    created() {
        this.fetchData();
        var vm = this;
        EventBus.$on("wordExplorer", function (word) {
            let query = `${vm.$globalConfig.apiServer}/api/explore/${vm.$route.params.queryTerm.trim()}`;
            vm.$http
                .get(query, {
                    headers: {
                        "Access-Control-Allow-Origin": "*",
                        "Content-Type": "application/json",
                    },
                })
                .then((response) => {
                    vm.vectors = response.data;
                    document.getElementById("overlay").style.display = "block";
                })
                .catch((error) => {
                    vm.error = error.toString();
                    console.log(error);
                });
        });
        EventBus.$on("closeWordExplorer", function () {
            vm.vectors = null;
            document.getElementById("overlay").style.display = "none";
        });
    },
    methods: {
        fetchData() {
            this.loading = true;
            let query = `${this.$globalConfig.apiServer}/api/mot/${this.$route.params.queryTerm.trim()}`;
            this.$http
                .get(query, {
                    headers: {
                        "Access-Control-Allow-Origin": "*",
                        "Content-Type": "application/json",
                    },
                })
                .then((response) => {
                    this.atHome = false;
                    EventBus.$emit("OffHome");
                    this.results = response.data;
                    this.totalResults = this.results.dictionaries.totalEntries;
                    this.totalDicos = this.results.dictionaries.totalDicos;
                    this.loading = false;
                })
                .catch((error) => {
                    this.error = error.toString();
                    console.log(error);
                });
        },
        pluralize(word, count) {
            if (count > 1) {
                return word + "s";
            }
            return word;
        },
    },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.hide-results {
    visibility: hidden;
}
#model1 {
    padding: 0;
}
/deep/ .dropdown-menu {
    -webkit-box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
    font-size: 100%;
    margin-left: 22px;
}
/deep/ #second-btn > button {
    font-size: 100% !important;
}
</style>