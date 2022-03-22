import { Component, OnInit, ViewChild } from '@angular/core';
import { PlayerRanking, GlobalRanking } from '../../interfaces/ranking';
import { Player } from '../../interfaces/player';
import { Challenge } from '../../interfaces/challenge';
import { PlayerService } from '../../services/player.service';
import { RankingService } from '../../services/ranking.service';
import { ChallengeService } from '../../services/challenge.service';
import { PlayerChallengeLaptime } from '../../interfaces/laptime';
import { MenuItem } from 'primeng/api';

@Component({
  selector: 'app-players',
  templateUrl: './players.component.html',
  styleUrls: ['./players.component.scss']
})
export class PlayersComponent implements OnInit {
  @ViewChild('dt_players_list') players_table: any;
  players: Player[] = [];
  globalRankings: GlobalRanking[] = [];
  selectedPlayer?: Player;
  playerRankings: PlayerRanking[] = [];
  challenges: Challenge[] = [];
  selectedPlayerRanking?: PlayerRanking;
  playerChallengeLaptimes: PlayerChallengeLaptime[] = [];
  speeddail_menu: MenuItem[] = [];

  constructor(
    private playerService: PlayerService,
    private rankingService: RankingService,
    private challengeService: ChallengeService
  ) { }

  ngOnInit(): void {
    this.refreshChallenges();
    this.refreshGlobalRanking();
    this.refreshPlayers();

    this.speeddail_menu = [
      {
        tooltipOptions: {
          tooltipLabel: "Refresh Screen",
          tooltipPosition: "top"
        },
        icon: 'pi pi-refresh',
        command: () => {
          this.refreshAll();
        }
      },
      {
        tooltipOptions: {
          tooltipLabel: "Export CSV",
          tooltipPosition: "top"
        },
        icon: 'pi pi-file',
        command: () => {
          this.players_table.exportCSV();
        }
      },
      {
        tooltipOptions: {
          tooltipLabel: "Open Home Screen",
          tooltipPosition: "top"
        },
        icon: 'pi pi-home',
        routerLink: ['/']
      }
    ]
  }

  selectPlayer(event: any) {
    this.selectedPlayerRanking = undefined;
    this.playerChallengeLaptimes = [];
    if (event) {
      this.selectedPlayer = event.data;
      this.refreshPlayerRankings();
    }
    else {
      this.selectedPlayer = undefined;
      this.playerRankings = [];
    }
  }

  selectPlayerRanking(event: any) {
    if (event) {
      this.selectedPlayerRanking = event.data;
      this.refreshPlayerChallengeLaptimes();
    }
    else {
      this.selectedPlayerRanking = undefined;
      this.playerChallengeLaptimes = [];
    }
  }

  refreshPlayers() {
    this.playerService
      .getPlayers()
      .subscribe(
        (players: Player[]) => {
          this.players = players;
        }
      );
  }

  refreshGlobalRanking() {
    this.rankingService
      .getGlobalRankings()
      .subscribe(
        (rankings: GlobalRanking[]) => {
          this.globalRankings = rankings;
        }
      );
  }

  refreshChallenges() {
    this.challengeService
      .getChallenges()
      .subscribe(
        (challenges: Challenge[]) => {
          this.challenges = challenges;
        }
      );
  }

  refreshPlayerRankings() {
    if (this.selectedPlayer) {
      this.playerService
        .getPlayerRankings(this.selectedPlayer.id)
        .subscribe(
          (pr: PlayerRanking[]) => {
            this.playerRankings = pr;
          }
        );
    }
  }

  refreshPlayerChallengeLaptimes() {
    if (this.selectedPlayer && this.selectedPlayerRanking) {
      this.playerService
        .getPlayerChallengeLaptimes(this.selectedPlayer.id, this.selectedPlayerRanking.challenge_id)
        .subscribe(
          (laptimes: PlayerChallengeLaptime[]) => {
            this.playerChallengeLaptimes = laptimes;
          }
        );
    }
  }

  refreshAll() {
    this.refreshPlayers();
    this.refreshGlobalRanking();
    this.refreshChallenges();
    this.refreshPlayerRankings();
    this.refreshPlayerChallengeLaptimes();
  }

}
