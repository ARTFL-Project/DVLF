<template>
    <div class="panel panel-default new-definition">
        <h3 style="text-align: center; margin-top: 0; margin-bottom: 10px; font-weight: 700">
            Soumettez votre exemple...
        </h3>
        <p>Entrez votre mot, votre exemple, et vos sources (si besoin est). Puis cliquez sur "Soumettre".</p>
        <p class="note-to-user">
            Par mesure de sécurité, tout lien HTML sera désactivé. <br />
            Seules les balises HTML <span style="font-family: monospace">&lt;i&gt;</span> (caractères en italiques) et
            <span style="font-family: monospace">&lt;b&gt;</span> (caractères gras) sont autorisées.<br />
            dans le corps de l'exemple.
        </p>
        <div class="row" style="margin-top: 20px">
            <div class="col-xs-12 col-sm-3 col-md-2">Terme:</div>
            <div class="col-xs-12 col-sm-8 col-md-10">
                <input
                    class="form-control"
                    type="text"
                    name="name"
                    style="max-width: 300px"
                    v-model="submission.term"
                />
            </div>
        </div>
        <div class="row">
            <div class="col-xs-12 col-sm-3 col-md-2" style="margin-top: 10px">Exemple:</div>
            <div class="col-xs-12 col-sm-8 col-md-6 col-lg-6" style="margin-top: 10px">
                <textarea id="definition-area" name="name" v-model="submission.example"></textarea><br />
            </div>
        </div>
        <div class="row">
            <div class="col-xs-12 col-sm-3 col-md-2" style="margin-top: 10px">Source:</div>
            <div class="col-xs-12 col-sm-8 col-md-6 col-lg-6" style="margin-top: 10px">
                <textarea id="source-area" rows="1" name="name" v-model="submission.source"></textarea><br />
            </div>
        </div>
        <div class="row">
            <div class="col-xs-12 col-sm-3 col-md-2" style="margin-top: 10px">Lien:</div>
            <div class="col-xs-12 col-sm-8 col-md-6 col-lg-6" style="margin-top: 10px">
                <textarea id="link-area" rows="1" name="name" v-model="submission.link"></textarea><br />
            </div>
        </div>

        <vue-recaptcha :sitekey="recaptchaKey" @verify="onVerify" style="margin-top: 10px"></vue-recaptcha>
        <br />
        <b-button variant="primary" disabled="disabled" v-if="!recaptchaDone">Soumettre</b-button>
        <b-button variant="primary" @click="submit()" v-if="recaptchaDone">
            Soumettre
            <span class="glyphicon glyphicon-repeat spinning" v-show="submitting"></span>
        </b-button>
    </div>
</template>

<script>
import VueRecaptcha from "vue-recaptcha";
import { EventBus } from "../main.js";

export default {
    name: "NewExample",
    components: {
        VueRecaptcha,
    },
    data() {
        return {
            currentTerm: this.$route.params.term,
            submission: { term: this.$route.params.term },
            submitting: false,
            recaptchaKey: this.$globalConfig.recaptchaKey,
            recaptchaDone: false,
        };
    },
    created() {
        EventBus.$emit("OffHome");
    },
    methods: {
        onVerify(response) {
            this.recaptchaDone = true;
            this.submission.recaptchaResponse = response;
        },
        submit() {
            var vm = this;
            if (this.recaptchaDone) {
                this.$http
                    .post(`${this.$globalConfig.apiServer}/api/submitExample`, this.submission)
                    .then(function (response) {
                        if (response.data.message === "success") {
                            vm.$router.push(`/mot/${vm.submission.term}`);
                        } else {
                            alert("Votre soumission a échouée.");
                        }
                    })
                    .catch((error) => {
                        this.error = error.toString();
                        console.log(error);
                    });
            }
        },
    },
};
</script>

<style scoped>
.new-definition {
    margin: 50px 10px;
    padding: 15px;
}
</style>
