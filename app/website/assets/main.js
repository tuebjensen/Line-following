import * as d3 from 'https://cdn.skypack.dev/pin/d3@v7.6.1-1Q0NZ0WZnbYeSjDusJT3/mode=imports,min/optimized/d3.js'
import { Subject, fromEvent, Observable, withLatestFrom, first, concatWith, mergeMap, switchMap, of, tap, throwError, retry, map, filter, merge, share, combineLatest } from 'https://cdn.skypack.dev/pin/rxjs@v7.5.7-j3yWv9lQY9gNeD9CyX5Y/mode=imports,min/optimized/rxjs.js'
import { parseMap } from './parse-map.js'
import { findPath } from './pathfinding.js'
// Handle WebSocket streams
const { clientState$, serverState$, updateClientState } = (function(){

    /**
     * The stream of websockets.
     * A new socket is created every time a socket closes or errors.
     */
    const socket$ = new Observable((subscriber) => {
        const socket = new WebSocket('ws://' + location.host + '/ws')
        subscriber.next(socket)
        subscriber.complete()
    }).pipe(
        switchMap(socket => merge(
            // emit the socket when it becomes open
            fromEvent(socket, 'open').pipe(
                tap(() => console.log('websocket opened')),
                map(() => socket),
            ),
            // on the first error, emit null, close the socket, and then throw an error
            fromEvent(socket, 'error').pipe(
                tap(() => console.log('eror')),
                first(),
                mergeMap(() =>
                    of(null).pipe(
                        tap(() => {
                            socket.close()
                        }),
                        concatWith(
                            throwError(() => new Error('WebSocket stream either closed or had an error!'))
                        )
                    )
                )
            ),
            // emit null if the socket is closed
            fromEvent(socket, 'close').pipe(
                tap(() => console.log('websocket closed')),
                map(() => null)
            )
        )),
        share()
    )
    
    socket$.subscribe(s => console.log('socket', s))

    /**
     * Stream of parsed messages coming from the sockets.
     */
    const message$ = socket$.pipe(
        filter(socket => socket),
        mergeMap(socket => fromEvent(socket, 'message')),
        map((msg) => JSON.parse(msg.data)),
        share()
    )
    
    message$.subscribe(m => console.log('message', m))

    /**
     * Stream which includes updates coming from the sockets targeting both client and server states.
     * The stream normally outputs
     *   1. Right after the connection has been made
     *   2. When the connection closes
     */
    const fullStateUpdate$ = merge(
        message$.pipe(
            filter(({ type, data }) => type === 'full-state-update'),
            map(message => message.data)
        ),
        socket$.pipe(
            filter(socket => socket === null),
            map(() => ({
                clientState: null,
                serverState: null
            }))
        )
    ).pipe(
        share()
    )

    /**
     * Stream which includes updates coming from the sockets targeting the server state.
     * The stream outputs often, e.g. when the Raspberry Pi leaves a node.
     * Outputs null when the socket is closed.
     */
    const serverStateUpdate$ = merge(
        fullStateUpdate$.pipe(
            map(data => data.serverState)
        ),
        message$.pipe(
            filter(message => message.type === 'server-state-update'),
            map(message => message.data)
        )
    ).pipe(
        share()
    )

    /**
     * Stream which includes updates coming from the sockets targeting the client state. 
     */
    const clientStateUpdate$ = merge(
        fullStateUpdate$.pipe(
            map(data => data.clientState)
        )
    ).pipe(
        share()
    )

    // make it possible for the client to emit new client state
    const clientStateSubject$ = new Subject()
    function updateClientState (clientState) {
        clientStateSubject$.next(clientState)
    }

    // if the client emits new states, send them to the server
    clientStateSubject$.pipe(
        withLatestFrom(socket$)
    ).subscribe(([clientState, socket]) => {
        socket?.send(JSON.stringify(clientState))
    })

    const clientState$ = merge(
        clientStateSubject$,
        clientStateUpdate$
    )

    return {
        updateClientState,
        clientState$,
        serverState$: serverStateUpdate$
    }
})()

// Setup D3 & the graph visualization.
;(function() { 
    const svg = d3.select('svg')
    const lineGroup = svg.append('g')
    const nodeGroup = svg.append('g')

    function displayMap (map) {
        const smallestDistance = Math.min(
            ...map.lineSegments.map(l =>
                Math.sqrt((l.start.x - l.end.x)**2 + (l.start.y - l.end.y)**2)
            )
        )
        const nodeRadius = smallestDistance / 2
        
        const minX = Math.min(...map.nodes.map(node => node.x)) - nodeRadius
        const minY = Math.min(...map.nodes.map(node => node.y)) - nodeRadius
        const maxX = Math.max(...map.nodes.map(node => node.x)) + nodeRadius
        const maxY = Math.max(...map.nodes.map(node => node.y)) + nodeRadius
        const width = maxX - minX
        const height = maxY - minY

        const line = lineGroup
            .selectAll('.line')
            .data(map.lineSegments)
            .join(
                enter => enter
                    .append('line')
            )
            .attr('x1', line => line.start.x)
            .attr('y1', line => line.start.y)
            .attr('x2', line => line.end.x)
            .attr('y2', line => line.end.y)
            .attr('stroke-width', smallestDistance * 0.1)
            .attr('stroke-linecap', 'round')
            .classed('line', true)        

        const node = nodeGroup
            .selectAll('.node')
            .data(map.nodes, node => node.id)
            .join(
                enter => enter
                    .append('g')
                    .call(g => {
                        g
                            .append('circle')
                            .attr('r', smallestDistance * 0.4)
                        g
                            .append('text')
                            .attr('dominant-baseline', 'central')
                            .attr('text-anchor', 'middle')
                            .attr('font-size', smallestDistance * 0.4 + 'px')
                            .text(node => node.id)
                    })
            )
            .attr('transform', node => `translate(${node.x},${node.y})`)
            .attr('r', smallestDistance * 0.4)
            .classed('destination', node => node.isPossibleDestination)
            .classed('node', true)


        svg.attr('viewBox', `${minX} ${minY} ${width} ${height}`)
    }

    const mapInput = document.getElementById('map-input')
    document.getElementById('map-update-form').addEventListener('submit', e => {
        e.preventDefault()
        const map = parseMap(mapInput.value)
        console.log(findPath(map, map.nodes[0].id, map.nodes.at(-1).id))
        //console.log(findPath(map, map.nodes[0].id, 20))

        console.log(map.lineSegments)
        displayMap(map)
    })
})()

window['updateClientState'] = updateClientState
clientState$.subscribe((state) => console.log('clientStateUpdated', state))
serverState$.subscribe((state) => console.log('serverStateUpdated', state))

// TODO handle map update