# Json format
This is the document that describes the json specifications to be passed to this tool for initial split of commit.  
First, here is an example of the correct json.

```json
{
  "contexts": [
    {
      "id": 1,
      "path": "./test",
      "code_infos": [
        {
          "code": "a = 1",
          "line_id": 10
        },
        {
          "code": "b = 2",
          "line_id": 11
        }
      ]
    }
  ],
  "chunk_relations": [
    {
      "first_chunk_id": 1,
      "first_chunk_type": "add",
      "second_chunk_id": 1,
      "second_chunk_type": "remove"
    }
  ],
  "chunk_sets": [
    {
      "add_chunks": [
        {
          "id": 1,
          "start_id": 1,
          "end_id": 2,
          "context_id": 1,
          "codes": [
            "c = 3",
            "d = 4"
          ]
        },
        {
          "id": 2,
          "start_id": 10,
          "end_id": 11,
          "context_id": 1,
          "codes": [
            "e = 5",
            "f = 6"
          ]
        }
      ],
      "remove_chunks": [
        {
          "start_id": 1,
          "end_id": 10,
          "context_id": 1
        },
        {
          "start_id": 20,
          "end_id": 30,
          "context_id": 1
        }
      ]
    }
  ]
}
```

This json consists of three major instances of `"contexts"`, `"chunk_relations"`, and `"chunk_sets"`.
We will Explain each of them.

## contexts
This is the array instance that contains information about the changed code and the surrounding code for a certain file.
(A `"contexts"` corresponds to a changed file.)
That is, the information that comes out with the native `git diff` command.

| key | type | description |
| --- | --- | --- |
| `"id"` | int | id of the first chunk |
| `"path"` | string | type of first chunk. This is either `"add"` or `"remove"` |
| `"code_infos"` | array | array of each code's information |

The content of `"code_infos"` is as follows.
### code_infos
| key | type | description |
| --- | --- | --- |
| `"code"` | int | content of code |
| `"line_id"` | string | line number of code |

## chunk_relations
This is the array instance that contains information about the relationship between chunks.
Describes the combination of two related chunks (Since it is a combination, the order of first and second is irrelevant.)

| key | type | description |
| --- | --- | --- |
| `"first_chunk_id"` | int | id of the first chunk |
| `"first_chunk_type"` | string | type of first chunk. This is either `"add"` or `"remove"` |
| `"second_chunk_id"` | int | id of the second chunk |
| `"second_chunk_type"` | string | type of the second chunk. This is either `"add"` of `"remove"` |

## chunk_sets
This is the array instance that contains information about the initial split of commit.
Each instance corresponds to a commit, which consists of a collection of add change chunks `"add_chunks"` and a collection of remove change chunks `"remove_chunks"`.

### add_chunks
| key | type | description |
| --- | --- | --- |
| `"id"` | int | id of the chunk(Please assign unique number starting from 1) |
| `"start_id"` | int | start line number of the chunk |
| `"end_id"` | int | end line number of the chunk |
| `"context_id"` | int | id of the context to which this chunk belongs |
| `"codes"` | array | type of the second chunk. This is either `"add"` of `"remove"` |

`"codes` instance is the array of content of codes like
```json
"codes": [
  "c = 3",
  "d = 4"
]
```

### remove_chunks
| key | type | description |
| --- | --- | --- |
| `"id"` | int | id of the chunk(Please assign unique number starting from 1) |
| `"start_id"` | int | start line number of the chunk |
| `"end_id"` | int | end line number of the chunk |
| `"context_id"` | int | id of the context to which this chunk belongs |
