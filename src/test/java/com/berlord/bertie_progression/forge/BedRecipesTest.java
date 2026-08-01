package com.berlord.bertie_progression.forge;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import org.junit.jupiter.api.Test;

import java.util.HashSet;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class BedRecipesTest {

    @Test
    void itemPredicatesMatchOnlyTheirConfiguredItem() {
        BedRecipes.StackPredicate glass = BedRecipes.item("minecraft:glass");
        assertTrue(glass.test(new ItemStack(Items.GLASS)));
        assertFalse(glass.test(new ItemStack(Items.STONE)));
        assertFalse(glass.test(ItemStack.EMPTY));
        assertEquals("minecraft:glass", glass.describe());
    }

    @Test
    void currentRecipeTableHasUniqueValidEntries() {
        HashSet<String> ids = new HashSet<>();
        for (BedRecipes.BedRecipe recipe : BedRecipes.RECIPES) {
            assertTrue(ids.add(recipe.id()), "duplicate recipe " + recipe.id());
            assertTrue(recipe.primary().count() > 0, recipe.id());
            assertTrue(recipe.resultCount() > 0, recipe.id());
            assertTrue(recipe.extraReturnCount() >= 0, recipe.id());
        }
        assertEquals(1, BedRecipes.RECIPES.size());
        assertEquals("utrem_jar", BedRecipes.RECIPES.getFirst().id());
    }
}
