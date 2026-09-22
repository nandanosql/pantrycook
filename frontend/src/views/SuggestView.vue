<template>
  <section>
    <div class="page-head">
      <div>
        <h1>What should we cook?</h1>
        <p class="lede">
          PantryCook ranks meals from what is already in the kitchen, then lists the gap to buy.
        </p>
      </div>
      <div class="actions">
        <button class="btn" :disabled="loading" @click="cook">
          {{ loading ? "Looking…" : "Suggest meals" }}
        </button>
        <button class="btn secondary" :disabled="loading" @click="loadSample">Load sample pantry</button>
      </div>
    </div>

    <div class="meta-row" v-if="constraints">
      <span class="chip">{{ pantryCount }} pantry items</span>
      <span class="chip">{{ constraints.servings }} servings</span>
      <span class="chip">{{ constraints.max_cook_minutes ? `Under ${constraints.max_cook_minutes} min` : "Any time" }}</span>
      <span v-for="tag in constraints.diet_tags" :key="tag" class="chip">{{ dietLabel(tag) }}</span>
      <router-link class="chip" to="/settings">Edit constraints</router-link>
    </div>

    <p v-if="error" class="banner error">{{ error }}</p>
    <p v-else-if="!result && pantryCount === 0" class="banner">
      Your pantry is empty. Add what you have, or load the sample kitchen and suggest from there.
    </p>
    <p v-else-if="result && !result.suggestions.length" class="banner">
      Nothing in the library fits these constraints. Relax the time limit or diet tags in Settings.
    </p>
    <p v-if="result && !result.llm_configured" class="muted">
      Suggestions are ranked offline. Add an API key if you want a short cook tip on each card.
    </p>

    <div class="stack" style="margin-top: 16px">
      <SuggestionCard v-for="item in result?.suggestions || []" :key="item.recipe_id + item.title" :suggestion="item" />
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import SuggestionCard from "../components/SuggestionCard.vue";
import { api } from "../api";
import { dietLabel } from "../constants";

const route = useRoute();
const loading = ref(false);
const error = ref("");
const result = ref(null);
const constraints = ref(null);
const pantryCount = ref(0);

async function loadMeta() {
  const [profile, pantry] = await Promise.all([api.constraints.get(), api.pantry.list()]);
  constraints.value = profile;
  pantryCount.value = pantry.length;
}

async function cook() {
  loading.value = true;
  error.value = "";
  try {
    await loadMeta();
    result.value = await api.suggest(6);
    pantryCount.value = result.value.pantry_count;
  } catch (err) {
    error.value = err.message || "Could not load suggestions.";
  } finally {
    loading.value = false;
  }
}

async function loadSample() {
  loading.value = true;
  error.value = "";
  try {
    const pantry = await api.pantry.sample();
    pantryCount.value = pantry.length;
    await cook();
  } catch (err) {
    error.value = err.message || "Could not load the sample pantry.";
    loading.value = false;
  }
}

onMounted(async () => {
  try {
    await loadMeta();
    if (route.query.cook === "1") await cook();
  } catch (err) {
    error.value = err.message || "The API is not reachable.";
  }
});
</script>
