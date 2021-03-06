<template>
    <div id="word-explorer" class="shadow-lg">
        <div id="explorer-title">
            <div id="title-close" @click="close">
                &times;
            </div>
            Exploration des usages de &laquo;<span id="headword">{{ headword }}</span>&raquo; à travers le temps
        </div>
        <div id="explorer-body">
            <b-row align-h="center">
                <b-col cols="12" md="6" v-if="vectors['1600']" style="margin-bottom: 20px;">
                    <b-card class="shadow-sm" style="height: 300px;" header="Entre 1600 et 1700">
                        <vue-word-cloud :words="vectors['1600']" :animation-overlap="0.2" :spacing="0.4" :font-size-ratio="0.3">
                            <template slot-scope="{text, weight, word}">
                                <div class="word-cloud" :title="weight" style="cursor: pointer;" @click="onWordClick(word)">
                                    {{ text }}
                                </div>
                            </template>
                        </vue-word-cloud>
                    </b-card>
                </b-col>
                <b-col cols="12" md="6" v-if="vectors['1700']" style="margin-bottom: 20px;">
                    <b-card class="shadow-sm" style="height: 300px;" header="Entre 1700 et 1800">
                        <vue-word-cloud :words="vectors['1700']" :animation-overlap="0.2" :spacing="0.4" :font-size-ratio="0.3">
                            <template slot-scope="{text, weight, word}">
                                <div class="word-cloud" :title="weight" style="cursor: pointer;" @click="onWordClick(word)">
                                    {{ text }}
                                </div>
                            </template>
                        </vue-word-cloud>
                    </b-card>
                </b-col>
                <b-col cols="12" md="6" v-if="vectors['1800']" style="margin-bottom: 20px;">
                    <b-card class="shadow-sm" style="height: 300px; min-width:40%" header="Entre 1800 et 1900">
                        <vue-word-cloud :words="vectors['1800']" :animation-overlap="0.2" :spacing="0.4" :font-size-ratio="0.3">
                            <template slot-scope="{text, weight, word}">
                                <div class="word-cloud" :title="weight" style="cursor: pointer;" @click="onWordClick(word)">
                                    {{ text }}
                                </div>
                            </template>
                        </vue-word-cloud>
                    </b-card>
                </b-col>
                <b-col cols="12" md="6" v-if="vectors['1900']">
                    <b-card class="shadow-sm" style="height: 300px; min-width: 40%" header="Entre 1900 et 2000">
                        <vue-word-cloud :words="vectors['1900']" :animation-overlap="0.2" :spacing="0.4" :font-size-ratio="0.3">
                            <template slot-scope="{text, weight, word}">
                                <div class="word-cloud" :title="weight" style="cursor: pointer;" @click="onWordClick(word)">
                                    {{ text }}
                                </div>
                            </template>
                        </vue-word-cloud>
                    </b-card>
                </b-col>
            </b-row>
            <div class="mt-2" style="text-align: center;">
                Données extraites à partir de la base de données <a href="https://artfl-project.uchicago.edu/content/artfl-frantext">ARTFL-Frantext</a>.
            </div>
            <b-button style="margin: 0 0 10px" variant="primary" @click="close()">
                Fermer
            </b-button>
        </div>

    </div>
</template>

<script>
import { EventBus } from "../main.js"
import VueWordCloud from "vuewordcloud"

export default {
    name: "WordExplorer",
    components: {
        [VueWordCloud.name]: VueWordCloud
    },
    props: {
        vectors: Object,
        headword: String
    },
    created() {
        let yOffset = window.pageYOffset
        if (yOffset > 0) {
            this.$nextTick(function() {
                document.getElementById(
                    "word-explorer"
                ).style.top = `${yOffset + 20}px`
            })
        } else {
            window.scrollTo({
                top: 0,
                left: 0,
                behavior: "smooth"
            })
        }
    },
    methods: {
        onWordClick(word) {
            this.$router.push(`/mot/${word[0]}`)
            this.close()
        },
        close() {
            EventBus.$emit("closeWordExplorer")
        }
    }
}
</script>

<style scoped>
#word-explorer {
    position: absolute;
    z-index: 100;
    width: 95%;
    left: 0;
    right: 0;
    margin: auto;
    background-color: #fff;
    border: 1px solid rgba(0, 0, 0, 0.125);
    border-radius: 0.25rem;
}
#explorer-title {
    position: relative;
    margin-bottom: 20px;
    background-color: #f0f0f0;
    border-bottom: 1px solid #eee;
    text-align: center;
    margin-top: 0;
    padding: 7px;
    font-weight: 700;
    font-size: 130%;
}
#headword {
    font-variant: small-caps;
    padding: 0 5px;
}
#title-close {
    position: absolute;
    right: -1px;
    top: -1px;
    border-radius: 0 4px 0 4px;
    background-color: rgba(21, 95, 131, 0.8) !important;
    color: #fff !important;
    padding: 0px 5px;
    cursor: pointer;
    font-size: 100%;
}
#explorer-body {
    padding: 15px;
}
.card-header {
    text-align: center;
    font-weight: 700;
}
.card-body {
    height: 250px;
    width: 100%;
    padding: 10px !important;
}
.word-cloud {
    color: rgb(21, 95, 131) !important;
    font-weight: 400;
    transition: all 200ms;
}
.btn-primary {
    background-color: rgba(21, 95, 131, 0.8) !important;
    color: #fff !important;
    float: right;
}
</style>
