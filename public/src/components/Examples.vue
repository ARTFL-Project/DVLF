<template>
    <transition appear name="fade">
        <b-card id="examples" class="shadow-sm" style="margin-top: 15px; animation-duration: 0.4s">
            <div id="examples-title">Exemples d'utilisation</div>
            <b-card class="example" v-for="(example, index) in examples" :key="index">
                <div class="example-score">
                    <img
                        src="../assets/images/baseline-arrow_upward-24px.svg"
                        class="up"
                        @click="vote(example.id, 'up')"
                    />
                    <span :id="example.id">{{ example.score }}</span>
                    <img
                        src="../assets/images/baseline-arrow_downward-24px.svg"
                        class="down"
                        @click="vote(example.id, 'down')"
                    />
                </div>
                <div class="example-content" v-html="example.content"></div>
                <div class="example-source" v-if="example.source">
                    Source :
                    <a
                        :href="example.link"
                        target="_blank"
                        rel="noreferrer"
                        v-if="example.link && example.link != 'http://' && !example.userSubmit"
                        >{{ example.source }}</a
                    >
                    <a :href="validateLink(example.link)" target="_blank" v-if="example.userSubmit">{{
                        example.source
                    }}</a>
                    <span v-if="!example.link || example.link == 'http://'">{{ example.source }}</span>
                </div>
                <div class="example-source" v-if="example.date">Contribué le {{ example.date }}</div>
            </b-card>
            <b-button-group style="margin: 0 10px 10px 10px" class="submit-btn" @click="addExample()">
                <b-button variant="primary">+</b-button>
                <b-button variant="primary"> Ajoutez votre exemple </b-button>
            </b-button-group>
        </b-card>
    </transition>
</template>

<script>
export default {
    name: "Examples",
    props: {
        examples: Array,
    },
    data() {
        return {
            headword: this.$route.params.queryTerm,
            voted: {},
        };
    },
    methods: {
        vote(id, vote) {
            if (id in this.voted) {
                alert("Vous avez déjà voté pour cet exemple.");
            } else {
                this.voted[id] = true;
                let query = `${this.$globalConfig.apiServer}/api/vote/${this.headword}/${id}/${vote}`;
                this.$http.get(query).then(function (response) {
                    document.getElementById(id).textContent = response.data.score;
                });
            }
        },
        addExample() {
            this.$router.push(`/exemple/${this.headword}`);
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
#examples-title {
    text-align: center;
    font-size: 110%;
    font-weight: 700;
    margin-top: 0px;
    padding: 5px;
    background-color: #f0f0f0;
    border-bottom: 1px solid #eee;
    margin-bottom: 10px;
}

.example {
    margin: 10px;
    padding: 10px;
}

.example-score {
    display: inline;
    font-family: serif;
    font-size: 110%;
    padding-right: 5px;
}

.example-score .glyphicon {
    color: #a8a8a8;
    cursor: pointer;
    transition: all 300ms;
}

.example-score .glyphicon:hover {
    color: black;
}

.up,
.down {
    display: inline-block;
    transition: all 0.2s;
}
.up {
    zoom: 0.8;
    margin-right: 5px;
}

.down {
    zoom: 0.8;
    margin-left: 5px;
}

.example-content {
    display: inline;
    padding-left: 5px;
    text-align: justify;
}

.up:hover,
.down:hover {
    background-color: #eee;
}

.example-source {
    display: inline-block;
    width: 100%;
    text-align: right;
    font-size: 85%;
}
</style>
