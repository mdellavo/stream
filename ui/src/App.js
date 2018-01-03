import './App.css';

import React, { Component } from 'react';
import Hls from 'hls.js';

import API from './API';


const AppState = {
    PLAYLISTS: "playlists",
    TRACKS: "tracks",
}

class Playlist extends Component {
    constructor(props) {
        super(props);
        this.handleLoadPlaylist = this.handleLoadPlaylist.bind(this);
    }
    
    handleLoadPlaylist(e) {
        e.preventDefault();
        this.props.onLoadPlaylist(this.props.playlist);
    }
    
    render() {
        const playlist = this.props.playlist;
        return (
            <div className="col-md-3">
              <div className="card">
                <div className="card-block">
                  <h4 className="card-title">{playlist.name}</h4>
                   <p className="card-text">
                    <em>Now:</em> {playlist.scheduled[0].track.artist} - {playlist.scheduled[0].track.title}<br/>
                    <em>Next:</em> {playlist.scheduled[1].track.artist} - {playlist.scheduled[1].track.title}
                  </p>
                  <a href={playlist.url} className="card-link" onClick={this.handleLoadPlaylist}>Listen Now!</a>
                </div>
              </div>
            </div>
        );
    }
}

function PlaylistRow(props) {
    var items = [];
    for (var i=0; i<props.row.length; i++) {
        items.push(
                <Playlist key={props.row[i].id} playlist={props.row[i]} onLoadPlaylist={props.onLoadPlaylist}/>
        );
    }
    return (
        <div className="row">
            {items}
        </div>
    );
}

class PlaylistsList extends Component {
    constructor(props) {
        super(props);
        this.state = {playlists: null};
        this.handlePlaylists = this.handlePlaylists.bind(this);
    }
    componentDidMount() {
        API.getPlaylists(this.handlePlaylists);
    }
    handlePlaylists(r) {
        if (r.status === "ok")
            this.setState({playlists: r.playlists});
    }
    render() {
        var rows = [];
        if (this.state.playlists) {
            for (var i=0; i<this.state.playlists.length; i+=3) {
                var slice = this.state.playlists.slice(i, i+3);
                rows.push(
                        <PlaylistRow key={i} row={slice} onLoadPlaylist={this.props.onLoadPlaylist}/>
                );
            }
        }

        return (
            <div className="container-fluid">
                {rows}    
            </div>
        );
    }   
}

class Player {

    opts = {
        debug: true,
        autoStartLoad: false,
    }
    
    constructor() {
        this.player = null;
        this.playing = false;
        this.hls = null;

        this.setupHls();
        
        this.onAttached = this.onAttached.bind(this);
        this.onLoaded = this.onLoaded.bind(this);
        this.onError = this.onError.bind(this);
        
    }

    setupHls() {

        if (this.hls)
            this.hls.destroy();
        
        this.hls = new Hls(this.opts);
        this.hls.on(Hls.Events.MEDIA_ATTACHED, this.onAttached);
        this.hls.on(Hls.Events.MANIFEST_PARSED, this.onLoaded);
        this.hls.on(Hls.Events.ERROR, this.onError);

        this.hls.attachMedia(this.player);

    }
    
    onAttached(event, data) {
		    console.log("player attached");
        this.onUpdate();
    }

    onLoaded(event, data) {
        console.log("manifest loaded, found " + data.levels.length + " quality level");
        this.hls.startLoad();
        this.playing = true;
        this.player.play();
        this.onUpdate();
    }

    onError(event, data) {
        console.log("error", event, data);
    }
    
    onUpdate() {}
    
    attach(ele) {
        this.player = ele;
    }

    play(playlist) {
        console.log("playing", playlist);
        this.setupHls();
        this.hls.loadSource(playlist.url);
        this.onUpdate();
    }

    pause() {
        this.playing = false;
        this.hls.stopLoad();
        this.player.pause();
        this.onUpdate();
    }

    isPlaying() {
        return this.playing;
    }

    toggle(playlist) {
        if (this.isPlaying())
            this.pause();
        else
            this.play(playlist);
    }
}

class PlayerView extends Component {
    constructor(props) {        
        super(props);
        this.onPlayerUpdate = this.onPlayerUpdate.bind(this);
        this.togglePlayback = this.togglePlayback.bind(this);
    }

    componentDidMount() {
        this.props.player.onUpdate = this.onPlayerUpdate;
    }

    onPlayerUpdate() {
        console.log("player update", this.props.player);
        this.setState({});
    }

    togglePlayback() {
        this.props.player.toggle(this.props.playlist);
    }
    
    render() {
        var isPlaying = this.props.player.isPlaying();
        return(
                <nav className="navbar navbar-toggleable-md fixed-bottom navbar-light bg-faded">
                <div className="container">
                  <form className="form-inline">
                    <button type="button" className="btn btn-outline-primary" onClick={this.togglePlayback}>
                        {isPlaying ? "Pause" : "Play"}
                    </button>
                  </form>
                
                <h4 className="navbar-brand">
                {this.props.playlist.name}
                </h4>

                <span className="navbar-text">
                    <em>Now:</em> {this.props.playlist.scheduled[0].track.artist} - {this.props.playlist.scheduled[0].track.title}<br/>
                    <em>Next:</em> {this.props.playlist.scheduled[1].track.artist} - {this.props.playlist.scheduled[1].track.title}
                </span>
                </div>
                </nav>
        );
    }
}

class App extends Component {
    
    constructor(props) {
        super(props);
        this.state = {status: null, selected: AppState.PLAYLISTS, playlist: null};
        
        this.handleStatus = this.handleStatus.bind(this);
        this.handleStatusError = this.handleStatusError.bind(this);
        this.select = this.select.bind(this);
        this.selectPlaylists = this.selectPlaylists.bind(this);
        this.selectTracks = this.selectTracks.bind(this);
        this.handleLoadPlaylist = this.handleLoadPlaylist.bind(this);

        this.player = new Player();
    }
    
    componentDidMount() {
        API.checkStatus(this.handleStatus, this.handleStatusError);

        const ele = document.getElementById("player");
        this.player.attach(ele);

    }

    select(e, selected) {
        e.preventDefault();
        this.setState({selected: selected});
    }
    
    selectPlaylists(e) {
        this.select(e, AppState.PLAYLISTS);
    }

    selectTracks(e) {
        this.select(e, AppState.TRACKS);
    }

    handleStatus(r) {
        this.setState({status: true});
    }

    handleStatusError(r) {
        this.setState({status: false});
    }

    handleLoadPlaylist(playlist) {
        this.setState({playlist: playlist});
        this.player.play(playlist);
    }
    
    render() {

        let body = null;
        if (this.state.selected === AppState.PLAYLISTS) {
            body = <PlaylistsList onLoadPlaylist={this.handleLoadPlaylist}/>;
        } else if (this.state.selected === AppState.TRACKS) {
        }

        let player = null;
        if (this.state.playlist) {
            player = <PlayerView player={this.player} playlist={this.state.playlist}/>;
        }
        
        return (            
            <div>
                <nav className="navbar navbar-toggleable-md fixed-top navbar-light bg-faded">
                     <ul className="navbar-nav">
                        <li className="nav-item"><a href="#" className="nav-link" onClick={this.selectPlaylists}>Playlists</a></li>
                        <li className="nav-item"><a href="#" className="nav-link" onClick={this.selectTracks}>Tracks</a></li>
                     </ul>
                </nav>
                {body}
                <video id="player" style={{display: 'none'}}/>                
                {player}
            </div>
        );
    }
}

export default App;
