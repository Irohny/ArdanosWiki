from dataclasses import dataclass, field


@dataclass(frozen=True)
class KampagneConfig:
    campaign_id: str
    campaign_name: str
    alias: str


@dataclass(frozen=True)
class PlayerAccessConfig:
    name: str
    user_name: str
    role: str
    campaigns: tuple[KampagneConfig, ...] = field(default_factory=tuple)
    charakter: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PlayerAccessRegistryConfig:
    players: tuple[PlayerAccessConfig, ...] = field(default_factory=tuple)
    campaigns: tuple[KampagneConfig, ...] = field(default_factory=tuple)

    @property
    def all_campaigns(self) -> tuple[KampagneConfig, ...]:
        player_campaigns = tuple(
            campaign
            for player in self.players
            for campaign in player.campaigns
        )
        return (*self.campaigns, *player_campaigns)

    @property
    def campaign_labels(self) -> dict[str, str]:
        return {
            campaign.campaign_id: campaign.campaign_name
            for campaign in self.all_campaigns
        }

    @property
    def campaign_aliases(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for campaign in self.all_campaigns:
            aliases[campaign.campaign_name] = campaign.campaign_id
            aliases[campaign.alias] = campaign.campaign_id
        return aliases

    def for_user_name(self, user_name: str) -> PlayerAccessConfig | None:
        normalized = user_name.strip().casefold()
        return next(
            (
                player
                for player in self.players
                if player.user_name.strip().casefold() == normalized
            ),
            None,
        )