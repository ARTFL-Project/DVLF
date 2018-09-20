<template>
    <div style="padding: 10px; margin-top: 15px;">
        <b-row>
            <b-col sm="12" md="6" offset-md="3">
                <transition name="fade">
                    <h3 :class="{'hide-results': apropos}" style="text-align: center; animation-duration: 0.4s" v-show="!loading">
                        <b>{{ currentTerm }}</b>:
                        <span class="entry-total" v-show="totalResults > 0">
                            {{ totalResults }} {{ pluralize("entrée", totalResults) }} dans {{ totalDicos }} {{ pluralize("dictionnaire", totalDicos) }}
                        </span>
                    </h3>
                </transition>
            </b-col>
            <b-col sm="12" md="3">
                <div class="float-right d-none d-sm-inline shadow-sm">
                    <b-button-group class="submit-btn" size="sm">
                        <b-button variant="primary">+</b-button>
                        <b-dropdown variant="primary" right text="Contribuer au DVLF">
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
            <b-col sm="3" md="2" class="d.sm.none" style="margin-top: 15px;">
                <transition name="fade">
                    <word-wheel :headword="currentTerm" v-if="!loading" style="animation-duration: 0.4s"></word-wheel>
                </transition>
            </b-col>
            <b-col sm="6" md="7" v-if="!loading">
                <dictionary-entries :results="results.dictionaries" :fuzzy-results="results.fuzzyResults"></dictionary-entries>
                <syn-anto-nyms class="d-block d-sm-none" :synonyms="results.synonyms" :antonyms="results.antonyms"></syn-anto-nyms>
                <examples :examples="results.examples"></examples>
            </b-col>
            <transition name="fade">
                <b-col sm="3" class="d-none d-sm-block" style="margin-top: 15px; animation-duration: 0.4s" v-if="!loading">
                    <syn-anto-nyms :synonyms="results.synonyms" :antonyms="results.antonyms"></syn-anto-nyms>
                    <collocations :collocates="results.collocates" :headword="currentTerm"></collocations>
                    <nearest-neighbors :nearest-neighbors="results.nearestNeighbors" :headword="currentTerm"></nearest-neighbors>
                    <time-series :time-series="results.timeSeries" :headword="currentTerm"></time-series>
                </b-col>
            </transition>
        </b-row>
    </div>
</template>

<script>
import DictionaryEntries from "./DictionaryEntries.vue"
import SynAntoNyms from "./SynAntoNyms.vue"
import Collocations from "./Collocations.vue"
import NearestNeighbors from "./NearestNeighbors.vue"
import TimeSeries from "./TimeSeries.vue"
import Examples from "./Examples.vue"
import WordWheel from "./WordWheel.vue"
import { EventBus } from "../main.js"
require("vue2-animate/dist/vue2-animate.min.css")

export default {
    name: "Results",
    components: {
        DictionaryEntries,
        SynAntoNyms,
        Collocations,
        NearestNeighbors,
        TimeSeries,
        Examples,
        WordWheel
    },
    data: function() {
        return {
            currentTerm: this.$route.params.queryTerm,
            results: {},
            totalResults: 0,
            totalDicos: 0,
            atHome: true,
            apropos: false,
            loading: true
        }
    },
    created() {
        this.fetchData()
    },
    methods: {
        fetchData() {
            this.loading = true
            let query = `${
                this.$globalConfig.apiServer
            }/api/mot/${this.$route.params.queryTerm.trim()}`
            this.$http
                .get(query, {
                    headers: {
                        "Access-Control-Allow-Origin": "*",
                        "Content-Type": "application/json"
                    }
                })
                .then(response => {
                    this.atHome = false
                    EventBus.$emit("OffHome")
                    this.results = response.data
                    this.totalResults = this.results.dictionaries.totalEntries
                    this.totalDicos = this.results.dictionaries.totalDicos
                    this.loading = false
                })
                .catch(error => {
                    this.error = error.toString()
                    console.log(error)
                })
        },
        pluralize(word, count) {
            if (count > 1) {
                return word + "s"
            }
            return word
        }
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.hide-results {
    visibility: hidden;
}
/deep/ .dropdown-menu {
    -webkit-box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
}
</style>