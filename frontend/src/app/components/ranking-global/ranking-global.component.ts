import { Component, Input, OnInit } from '@angular/core';
import { GlobalRanking } from '../../interfaces/ranking';
import { Player } from '../../interfaces/player';

@Component({
  selector: 'app-ranking-global',
  templateUrl: './ranking-global.component.html',
  styleUrls: ['./ranking-global.component.css']
})
export class RankingGlobalComponent implements OnInit {
  @Input() globalRankings: GlobalRanking[] = [];
  @Input() players: Player[] = [];

  constructor() { }

  ngOnInit(): void {
  }

  public playerName(player_id: string): string {
    let p = this.players.find(p => p.id === player_id);
    if (p) return p.name;
    else return '--new player--';
  }

}
