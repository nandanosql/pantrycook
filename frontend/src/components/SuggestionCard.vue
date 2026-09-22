<template>
  <article class="card suggestion">
    <div class="score">
      <b>{{ percent }}%</b>
      <span>pantry match</span>
    </div>
    <div>
      <h2>{{ suggestion.title }}</h2>
      <p class="muted" style="margin: 6px 0 0">{{ suggestion.description }}</p>
      <div class="meta-row">
        <span class="chip">{{ totalTime }} min</span>
        <span class="chip">{{ suggestion.scaled_servings }} servings</span>
        <span v-for="tag in suggestion.diet_tags" :key="tag" class="chip">{{ dietLabel(tag) }}</span>
        <span v-if="suggestion.use_soon.length" class="chip soon">Use soon</span>
      </div>
      <div class="bar" aria-hidden="true"><span :style="{ width: percent + '%' }" /></div>
      <p class="why">{{ suggestion.why }}</p>

      <p class="group-label">In your pantry</p>
      <div class="meta-row" v-if="suggestion.matched_ingredients.length">
        <span
          v-for="item in suggestion.matched_ingredients"
          :key="item.name"
          class="chip good"
          :title="item.detail"
        >
          {{ item.name }}
          <template v-if="item.near_expiry"> · soon</template>
          <template v-if="item.optional"> · extra</template>
        </span>
      </div>
      <p v-else class="muted">Nothing matched yet.</p>

      <template v-if="suggestion.missing_ingredients.length">
        <p class="group-label">Still missing</p>
        <div class="meta-row">
          <span v-for="item in suggestion.missing_ingredients" :key="item.name" class="chip miss">
            {{ item.name }}
            <template v-if="item.quantity"> · {{ formatAmount(item.quantity, item.unit) }}</template>
            <template v-if="item.partial"> · short</template>
          </span>
        </div>
      </template>

      <template v-if="suggestion.shopping_delta.length">
        <p class="group-label">Shopping delta</p>
        <ul>
          <li v-for="line in suggestion.shopping_delta" :key="line.name + line.note">
            {{ line.name }}
            <template v-if="line.quantity != null"> — {{ formatAmount(line.quantity, line.unit) }}</template>
            <span class="muted"> ({{ line.note }})</span>
          </li>
        </ul>
      </template>

      <p v-if="suggestion.llm_tip" class="tip">{{ suggestion.llm_tip }}</p>

      <details v-if="suggestion.instructions.length">
        <summary>Cook it</summary>
        <ol class="steps">
          <li v-for="(step, index) in suggestion.instructions" :key="index">{{ step }}</li>
        </ol>
      </details>
    </div>
  </article>
</template>

<script setup>
import { computed } from "vue";
import { dietLabel, formatAmount } from "../constants";

const props = defineProps({
  suggestion: { type: Object, required: true },
});

const percent = computed(() => Math.round((props.suggestion.coverage || 0) * 100));
const totalTime = computed(() => (props.suggestion.prep_minutes || 0) + (props.suggestion.cook_minutes || 0));
</script>
