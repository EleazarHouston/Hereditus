import re

import pytest
from playwright.sync_api import Page, expect, sync_playwright

from main_game.models import Colony
from main_game.tests.factories import DiscoveryFactory, GameFactory, UserFactory

PASSWORD = "test-password"


def login(page: Page, base_url: str, username: str) -> None:
    page.goto(f"{base_url}/login")
    page.locator("#id_username").fill(username)
    page.locator("#id_password").fill(PASSWORD)
    page.get_by_role("button", name="Login").click()
    expect(page).to_have_url(re.compile(r"/play/$"))


def join_game(page: Page, game_description: str, colony_name: str) -> None:
    page.get_by_role("button", name=game_description).click()
    form = page.locator(".new-colony-form")
    form.locator(".new-colony-input").fill(colony_name)
    form.get_by_role("button", name="New Colony").click()
    expect(page.get_by_role("status")).to_contain_text("Colony created.")


def assign_first_torb(page: Page, action: str) -> None:
    page.locator(".torb-checkbox").first.check()
    page.get_by_role("button", name=action, exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Colony action updated.")


def end_turn(page: Page) -> None:
    page.locator("#endTurnButton").click()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_two_players_advance_research_scout_and_attack_through_browser(live_server):
    game = GameFactory(description="Browser campaign", starting_torbs=2)
    first_user = UserFactory(username="browser-one")
    second_user = UserFactory(username="browser-two")
    discovery = DiscoveryFactory(
        name="Field Genomics",
        description="Decode useful traits.",
        research_cost=10,
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        first_context = browser.new_context()
        second_context = browser.new_context()
        first_page = first_context.new_page()
        second_page = second_context.new_page()

        login(first_page, live_server.url, first_user.username)
        login(second_page, live_server.url, second_user.username)
        join_game(first_page, game.description, "First Colony")
        join_game(second_page, game.description, "Second Colony")

        first_storage = first_context.storage_state()
        second_storage = second_context.storage_state()
        first_context.close()
        second_context.close()
        browser.close()

    first_colony = Colony.objects.get(player__user=first_user, game=game)
    second_colony = Colony.objects.get(player__user=second_user, game=game)
    first_colony.lab.science_points = 20
    first_colony.lab.save(update_fields=["science_points"])

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        first_context = browser.new_context(storage_state=first_storage)
        second_context = browser.new_context(storage_state=second_storage)
        first_page = first_context.new_page()
        second_page = second_context.new_page()

        first_page.goto(f"{live_server.url}/play/{first_colony.pk}/overview/")
        second_page.goto(f"{live_server.url}/play/{second_colony.pk}/overview/")
        assign_first_torb(first_page, "Enlist")
        assign_first_torb(second_page, "Gather")
        end_turn(first_page)
        end_turn(second_page)

        first_page.reload()
        expect(first_page.get_by_text("Year: 2", exact=True)).to_be_visible()
        expect(second_page.get_by_text("Year: 2", exact=True)).to_be_visible()

        first_page.get_by_role("link", name="Lab").click()
        first_page.locator("#science-points-used").fill("10")
        first_page.get_by_role("button", name="Make Mutagen").click()
        expect(first_page.get_by_role("status")).to_contain_text("Lab action completed.")
        discovery_card = first_page.locator(".discovery-card", has_text=discovery.name)
        discovery_card.get_by_role("button", name="Unlock").click()
        expect(first_page.get_by_role("status")).to_contain_text("Lab action completed.")
        expect(
            first_page.locator(".discovery-card.unlocked", has_text=discovery.name)
        ).to_be_visible()

        first_page.get_by_role("link", name="Army").click()
        target_selector = f"input[name=selected_colony][value='{second_colony.pk}']"
        first_page.locator(f"form:has({target_selector}) button[value=scout]").click()
        expect(first_page.get_by_role("status")).to_contain_text("Army orders updated.")
        end_turn(first_page)
        second_page.reload()
        end_turn(second_page)

        first_page.reload()
        expect(first_page.get_by_text(second_colony.name, exact=True)).to_be_visible()
        first_page.locator(f"form:has({target_selector}) button[value=attack]").click()
        expect(first_page.get_by_role("status")).to_contain_text("Army orders updated.")
        end_turn(first_page)
        second_page.reload()
        end_turn(second_page)

        first_page.reload()
        expect(first_page.get_by_text("glorious victory", exact=False)).to_be_visible()
        first_page.get_by_role("link", name="Overview").click()
        expect(first_page.get_by_text("Year: 4", exact=True)).to_be_visible()

        first_context.close()
        second_context.close()
        browser.close()
