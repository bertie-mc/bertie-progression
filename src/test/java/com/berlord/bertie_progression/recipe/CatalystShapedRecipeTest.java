package com.berlord.bertie_progression.recipe;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingBookCategory;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.ShapedRecipePattern;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class CatalystShapedRecipeTest {

    @Test
    void catalystReturnsOneItemWhileOrdinaryInputsAreConsumed() {
        Ingredient catalyst = Ingredient.of(Items.DIAMOND);
        ShapedRecipePattern pattern = ShapedRecipePattern.of(
                Map.of('c', catalyst, 'i', Ingredient.of(Items.STICK)), "ci");
        CatalystShapedRecipe recipe = new CatalystShapedRecipe("", CraftingBookCategory.MISC,
                pattern, new ItemStack(Items.MAP), true, catalyst);
        CraftingInput input = CraftingInput.of(2, 1,
                List.of(new ItemStack(Items.DIAMOND, 4), new ItemStack(Items.STICK, 2)));

        var remaining = recipe.getRemainingItems(input);
        assertTrue(remaining.get(1).isEmpty());
        assertTrue(remaining.getFirst().is(Items.DIAMOND));
        assertEquals(1, remaining.getFirst().getCount());
    }
}
