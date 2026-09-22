<template>
  <section>
    <div class="page-head">
      <div>
        <h1>Constraints</h1>
        <p class="lede">
          One profile for this server. v0.1 has no accounts — anyone who can open the site can change it.
        </p>
      </div>
    </div>

    <p v-if="error" class="banner error">{{ error }}</p>
    <p v-if="notice" class="banner ok">{{ notice }}</p>

    <form class="panel form-grid" @submit.prevent="save">
      <div>
        <span>Diet</span>
        <p class="muted">Vegan is stricter than vegetarian. Pescatarian still includes vegetarian meals.</p>
        <div class="toggle-row">
          <button
            v-for="tag in DIET_TAGS"
            :key="tag.id"
            type="button"
            class="toggle"
            :class="{ on: form.diet_tags.includes(tag.id) }"
            @click="toggle(tag.id)"
          >
            {{ tag.label }}
          </button>
        </div>
      </div>

      <div class="row">
        <label class="field">
          <span>Max total time (prep + cook)</span>
          <input v-model.number="form.max_cook_minutes" type="number" min="5" max="300" :disabled="noLimit" />
        </label>
        <label class="check">
          <input v-model="noLimit" type="checkbox" />
          No time limit
        </label>
        <label class="field">
          <span>Servings</span>
          <input v-model.number="form.servings" type="number" min="1" max="12" />
        </label>
      </div>

      <div>
        <span>Skip these ingredients</span>
        <div class="row" style="margin-top: 8px">
          <label class="field grow">
            <span class="muted">Press enter to add</span>
            <input v-model="excludeDraft" placeholder="peanut, mushroom…" @keydown.enter.prevent="addExclude" />
          </label>
          <button class="btn secondary" type="button" @click="addExclude">Add</button>
        </div>
        <div class="meta-row">
          <span v-for="item in form.exclude_ingredients" :key="item" class="chip miss">
            {{ item }}
            <button type="button" :aria-label="`Remove ${item}`" @click="removeExclude(item)">×</button>
          </span>
        </div>
      </div>

      <div class="actions">
        <button class="btn" type="submit">Save constraints</button>
        <router-link class="btn secondary" to="/">Back to tonight</router-link>
      </div>

      <p class="muted" v-if="health">
        <template v-if="health.llm_configured">Cook tips are on. Suggestions can include a short note from your configured model.</template>
        <template v-else>Cook tips are off. Set OPENAI_API_KEY (or a compatible OPENAI_BASE_URL) and restart the API.</template>
      </p>
    </form>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../api";
import { DIET_TAGS } from "../constants";

const error = ref("");
const notice = ref("");
const noLimit = ref(false);
const excludeDraft = ref("");
const health = ref(null);
const form = reactive({
  diet_tags: [],
  max_cook_minutes: 45,
  servings: 2,
  exclude_ingredients: [],
});

function toggle(id) {
  if (form.diet_tags.includes(id)) form.diet_tags = form.diet_tags.filter((tag) => tag !== id);
  else form.diet_tags = [...form.diet_tags, id];
}

function addExclude() {
  const value = excludeDraft.value.trim().toLowerCase();
  if (!value || form.exclude_ingredients.includes(value)) {
    excludeDraft.value = "";
    return;
  }
  form.exclude_ingredients = [...form.exclude_ingredients, value];
  excludeDraft.value = "";
}

function removeExclude(item) {
  form.exclude_ingredients = form.exclude_ingredients.filter((value) => value !== item);
}

async function save() {
  error.value = "";
  notice.value = "";
  try {
    const saved = await api.constraints.save({
      diet_tags: form.diet_tags,
      max_cook_minutes: noLimit.value ? null : Number(form.max_cook_minutes) || null,
      servings: Number(form.servings) || 2,
      exclude_ingredients: form.exclude_ingredients,
    });
    apply(saved);
    notice.value = "Saved.";
  } catch (err) {
    error.value = err.message || "Could not save constraints.";
  }
}

function apply(profile) {
  form.diet_tags = [...(profile.diet_tags || [])];
  form.servings = profile.servings;
  form.exclude_ingredients = [...(profile.exclude_ingredients || [])];
  noLimit.value = profile.max_cook_minutes == null;
  form.max_cook_minutes = profile.max_cook_minutes || 45;
}

onMounted(async () => {
  try {
    const [profile, status] = await Promise.all([api.constraints.get(), api.health()]);
    apply(profile);
    health.value = status;
  } catch (err) {
    error.value = err.message || "The API is not reachable.";
  }
});
</script>
