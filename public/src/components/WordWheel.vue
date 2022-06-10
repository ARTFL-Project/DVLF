<template>
    <b-card id="wordwheel" class="shadow-sm">
        <h4 class="index">Index</h4>
        <b-list-group>
            <b-list-group-item
                :to="`/mot/${word}`"
                :id="word"
                class="list-group-item wordwheel-item"
                :href="`/mot/${word}`"
                :class="{ active: word === headword }"
                v-for="(word, index) in wordwheel"
                :key="index"
            >
                {{ word }}
            </b-list-group-item>
        </b-list-group>
    </b-card>
</template>

<script>
import VueScrollTo from "vue-scrollto";

export default {
    name: "WordWheel",
    props: {
        headword: String,
    },
    data() {
        return {
            wordwheel: [],
            firstLoad: true,
            startIndex: 0,
            endIndex: 0,
            currentFirst: null,
            loading: false,
            upperLimit: 2000,
        };
    },
    computed: {
        lowerLimit: function () {
            let wordwheelSize = this.wordwheel.length || 0;
            return wordwheelSize * 40 - 3000;
        },
    },
    created() {
        this.fetchData();
    },
    methods: {
        fetchData() {
            this.loading = true;
            let vm = this;
            this.$http
                .get(`${this.$globalConfig.apiServer}/api/wordwheel?headword=${this.headword}`, {
                    headers: {
                        "Access-Control-Allow-Origin": "*",
                        "Content-Type": "application/json",
                    },
                })
                .then(function (response) {
                    vm.wordwheel = response.data.words;
                    vm.startIndex = response.data.startIndex;
                    vm.endIndex = response.data.endIndex;
                    vm.$nextTick(function () {
                        let options = {
                            container: "#wordwheel .list-group",
                            duration: 5,
                            offset: -366,
                        };
                        let element = document.getElementById("wordwheel").querySelector(".active");
                        VueScrollTo.scrollTo(element, options);
                        vm.loading = false;
                        vm.infiniteScroll();
                    });
                })
                .catch((error) => {
                    this.error = error.toString();
                    console.log(error);
                });
        },
        infiniteScroll() {
            var vm = this;
            this.$nextTick(function () {
                let wordWheel = this.$el.querySelector(".list-group");
                let timeout;
                wordWheel.onscroll = function () {
                    if (timeout) {
                        window.clearTimeout(timeout);
                    }

                    timeout = window.setTimeout(function () {
                        let scrollPosition = wordWheel.scrollTop;
                        if (!vm.loading && !vm.firstLoad) {
                            if (scrollPosition < vm.upperLimit) {
                                vm.addBefore(vm);
                            } else if (scrollPosition > vm.lowerLimit) {
                                vm.addAfter(vm);
                            }
                        }
                        if (vm.firstLoad) {
                            vm.firstLoad = false;
                        }
                    }, 2);
                };
            });
        },
        addBefore(vm) {
            vm.loading = true;
            vm.currentFirst = vm.wordwheel[50]; // We get the 50st since this where we trigger the load (50*40px)
            vm.$http
                .get(
                    `${vm.$globalConfig.apiServer}/api/wordwheel?startIndex=${vm.startIndex}&endIndex=${vm.endIndex}&position=before`
                )
                .then(function (response) {
                    vm.wordwheel.unshift(...response.data.words);
                    vm.startIndex = response.data.startIndex;
                    vm.endIndex = response.data.endIndex;
                    vm.loading = false;
                    vm.$nextTick(function () {
                        let options = {
                            container: "#wordwheel .list-group",
                            duration: 1,
                            offset: -24,
                        };
                        let element = document.getElementById(vm.currentFirst);
                        VueScrollTo.scrollTo(element, options);
                    });
                })
                .catch((error) => {
                    vm.error = error.toString();
                    console.log(error);
                });
        },
        addAfter(vm) {
            vm.loading = true;
            vm.$http
                .get(
                    `${vm.$globalConfig.apiServer}/api/wordwheel?startIndex=${vm.startIndex}&endIndex=${vm.endIndex}&position=after`
                )
                .then(function (response) {
                    vm.wordwheel.push(...response.data.words);
                    vm.startIndex = response.data.startIndex;
                    vm.endIndex = response.data.endIndex;
                    vm.loading = false;
                })
                .catch((error) => {
                    vm.error = error.toString();
                    console.log(error);
                });
        },
    },
};
</script>

<style scoped>
.list-group {
    margin-top: -10px;
    max-height: 800px;
    overflow-y: scroll;
}
.list-group-item {
    border-width: 1px 0px;
}
.list-group-item.active {
    background-color: rgba(21, 95, 131, 0.85) !important;
    border-color: rgba(21, 95, 131, 0.85) !important;
    color: #fff !important;
}
#up {
    padding: 4px 10px 0px;
}
#up,
#down {
    display: inline-block;
    width: 100%;
    border-width: 0px;

    background-color: #f8f8f8;
}
#down {
    padding: 0px 10px;
    transform: rotate(180deg);
}
</style>
