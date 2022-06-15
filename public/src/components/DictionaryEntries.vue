<template>
    <div>
        <div style="margin: 15px 0px" v-if="results.totalDicos == 0">
            Il n'existe aucune entrée pour le terme
            <b>{{ currentTerm }}</b>
            <b-button style="margin-left: 10px" type="button" @click="define()">
                <span class="glyphicon glyphicon-plus add-button"></span>
                Ajoutez votre définition
            </b-button>
        </div>
        <div v-if="results.totalEntries < 2">
            <div v-if="fuzzyResults.length > 0">
                Voici des termes similaires présents dans l'index:<br />
                <div style="display: inline-block" v-for="(word, index) in fuzzyResults" :key="index">
                    <router-link :to="`/mot/${word.word}`">{{ word.word }}&nbsp;&nbsp;</router-link>
                </div>
            </div>
            <div v-if="fuzzyResults.length == 0">Aucun terme similaire dans l'index</div>
        </div>
        <transition-group appear name="fade">
            <b-card
                class="dico shadow-sm mt-3"
                style="animation-duration: 0.4s"
                v-for="(dico, dicoIndex) in results.data"
                :key="dicoIndex"
            >
                <b-row class="dico-title text-center">
                    <b-col cols="1" class="arrow" @click="toggleEntry(dicoIndex)">
                        <img
                            class="down-arrow"
                            src="../assets/images/baseline-keyboard_arrow_down-24px.svg"
                            v-show="dico.show"
                        />
                        <img
                            class="right-arrow"
                            src="../assets/images/baseline-keyboard_arrow_right-24px.svg"
                            v-show="!dico.show"
                        />
                    </b-col>
                    <b-col cols="9" sm="10" class="dico-label" @click="toggleEntry(dicoIndex)">
                        {{ dico.label }}
                    </b-col>
                    <b-col cols="1">
                        <span class="badge">{{ dico.contentObj.length }}</span>
                    </b-col>
                </b-row>
                <div class="dico-entries" :class="{ showdico: dico.show }">
                    <div
                        class="entry"
                        style="padding-right: 10px"
                        v-for="(entry, index) in dico.contentObj"
                        :key="index"
                        :class="{ tlfi: dico.name === 'tlfi' }"
                    >
                        <div v-html="entry.content"></div>
                        <div v-if="dico.name == 'userSubmit' && entry.link.length > 0">
                            Source: <a :href="validateLink(entry.link)" target="_blank">{{ entry.source }}</a>
                        </div>
                        <div class="example-source" v-if="entry.date">Contribuée le {{ entry.date }}</div>
                        <hr
                            v-if="!index == dico.contentObj.length - 1"
                            style="width: 50%; margin-top: 15px; margin-bottom: 5px; border-color: #ddd"
                        />
                    </div>
                    <div class="tlfi-link" v-if="dico.name === 'tlfi'">
                        <a :href="`http://www.cnrtl.fr/definition/${encodeURIComponent(currentTerm)}`" target="_blank"
                            >=> Voir la définition complète au CNRTL</a
                        >
                    </div>
                </div>
                <div class="m-2" v-if="dico.name === 'userSubmit'">
                    <b-button-group class="submit-btn" @click="define()">
                        <b-button variant="primary">+</b-button>
                        <b-button variant="primary"> Ajoutez votre définition </b-button>
                    </b-button-group>
                </div>
            </b-card>
        </transition-group>
    </div>
</template>

<script>
export default {
    name: "DictionaryEntries",
    props: {
        results: Object,
        fuzzyResults: Array,
    },
    data: function () {
        return {
            currentTerm: this.$route.params.queryTerm,
        };
    },
    methods: {
        define: function () {
            this.$router.push(`/definition/${this.currentTerm}`);
        },
        toggleEntry(dicoIndex) {
            let targetElement = event.srcElement;
            if (
                targetElement.classList.contains("d-sm-none") ||
                targetElement.classList.contains("right-arrow") ||
                targetElement.classList.contains("down-arrow") ||
                targetElement.classList.contains("arrow") ||
                targetElement.classList.contains("badge")
            ) {
                targetElement = targetElement.parentNode.parentNode.parentNode;
            } else if (targetElement.classList.contains("dico-label")) {
                targetElement = targetElement.parentNode.parentNode;
            }
            let entry = targetElement.querySelector(".dico-entries");
            let arrows = targetElement.querySelector(".arrow");
            if (!entry.classList.contains("showdico")) {
                entry.classList.add("showdico");
                arrows.querySelector(".right-arrow").style.display = "none";
                arrows.querySelector(".down-arrow").style.display = "initial";
            } else {
                entry.classList.remove("showdico");
                arrows.querySelector(".down-arrow").style.display = "none";
                arrows.querySelector(".right-arrow").style.display = "initial";
            }
        },
        validateLink(link) {
            if (link.search(/^https?:\/\//) == -1) {
                link = `https://${link}`;
            }
            return link;
        },
    },
};
</script>

<style scoped>
.xml-prononciation::before {
    content: "(";
}

.xml-prononciation::after {
    content: ")\A";
}

.xml-nature {
    font-style: italic;
}

.xml-indent,
.xml-variante {
    display: block;
}

.xml-variante {
    padding-top: 10px;
    padding-bottom: 10px;
    text-indent: -1.3em;
    padding-left: 1.3em;
}

.xml-variante::before {
    counter-increment: section;
    content: counter(section) ")\00a0";
    font-weight: 700;
}

:not(.xml-rubrique) + .xml-indent {
    padding-top: 10px;
}

.xml-indent {
    padding-left: 1.3em;
}

.xml-cit {
    padding-left: 2.3em;
    display: block;
    text-indent: -1.3em;
}

.xml-indent > .xml-cit {
    padding-left: 1em;
}

.xml-cit::before {
    content: "\2012\00a0\00ab\00a0";
}

.xml-cit::after {
    content: "\00a0\00bb\00a0("attr(aut) "\00a0"attr(ref) ")";
    font-variant: small-caps;
}

.xml-rubrique {
    display: block;
    margin-top: 20px;
}

.xml-rubrique::before {
    content: attr(nom);
    font-variant: small-caps;
    font-weight: 700;
}

.xml-corps + .xml-rubrique {
    margin-top: 10px;
}

.dico {
    overflow: hidden;
}

.showdico {
    display: block !important;
}

.dico-title {
    text-align: center;
    font-size: 110%;
    font-weight: 700;
    margin-top: 0px;
    padding: 5px;
    background-color: #f0f0f0;
    border-bottom: 1px solid #eee;
}

.dico-label,
.arrow {
    cursor: pointer;
}

.dico-entries {
    text-align: justify;
    margin-top: 10px;
    line-height: 150%;
    display: none;
    transition: all 200ms;
}

.entry {
    /*max-height: 400px;*/
    overflow-y: auto;
    padding: 0 10px 10px 10px;
    font-size: inherit !important;
}

.entry.tlfi {
    max-height: 150px;
    overflow: hidden;
}

.arrow .glyphicon {
    vertical-align: middle;
    font-size: 80%;
}

.tlfi-link {
    float: left;
    padding: 10px 10px 10px 10px;
}

.tlfi-link a {
    cursor: pointer;
}
.badge {
    background-color: #fff;
    color: rgba(21, 95, 131, 0.85);
    font-family: initial;
    font-size: 90%;
    border-radius: 90%;
    padding: 0.2rem 0.4rem;
    margin-top: 3px;
    display: inline-block;
}
@media only screen and (max-width: 1200px) {
    .badge {
        margin-left: -10px;
    }
}
@media only screen and (max-width: 768px) {
    .badge {
        margin-left: 0;
    }
}
</style>


