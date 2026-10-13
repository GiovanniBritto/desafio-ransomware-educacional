# Relatório técnico — criptografia e recuperação de arquivos

## Objetivo

Demonstrar criptografia simétrica e recuperação de conteúdo com os scripts `encrypter.py` e `decrypter.py`, mantendo o exercício limitado a um exemplo fictício que acompanha o projeto.

## Ambiente observado

| Item | Valor |
| --- | --- |
| Data da validação | 13/10/2026 |
| Sistema operacional | Windows |
| Python | 3.12.14 |
| Biblioteca | cryptography 50.0.2 |
| Entrada | `laboratorio/original/exemplo.txt` |
| Diretório de saídas | `laboratorio/gerados/` |

## Implementação

A entrada contém texto fictício conhecido. Antes da criptografia, o programa verifica esse conteúdo e seu tamanho. Quebras de linha LF e CRLF são aceitas e os bytes originais são preservados na recuperação.

A chave é gerada pela biblioteca na execução. O arquivo original é aberto somente para leitura; a chave e a cópia criptografada são gravadas em novos arquivos. Os nomes de saída são fixos, e a criação exclusiva impede sobrescrever um arquivo existente.

Na recuperação, Fernet autentica o token antes de disponibilizar o conteúdo. O programa compara o resultado com o exemplo original e, somente após essa validação, cria uma cópia recuperada. O hash SHA-256 é exibido para registrar a correspondência.

Os caminhos são derivados da localização dos scripts, em vez do diretório atual do terminal. Assim, executar o programa a partir de outra pasta não muda sua entrada nem seu destino. O projeto também recusa caminhos de saída fora dos nomes permitidos, links simbólicos e pontos de redirecionamento detectados.

## Resultados dos testes de integração

| Caso | Resultado |
| --- | --- |
| Criptografia e recuperação com original intacto | Aprovado |
| Repetição da criptografia sem sobrescrita | Aprovado |
| Chave incorreta sem geração de cópia recuperada | Aprovado |
| Token adulterado sem geração de cópia recuperada | Aprovado |
| Exemplo modificado recusado | Aprovado |
| Entrada acima de 4 KiB recusada | Aprovado |
| Arquivo recuperado existente preservado | Aprovado |
| Descriptografia anterior à criptografia informa erro | Aprovado |
| Arquivos externos e diretório atual preservados | Aprovado |
| Quebras de linha CRLF preservadas | Aprovado |
| Caminho arbitrário recusado e chave ausente da saída do terminal | Aprovado |

Foram executados 11 testes, todos aprovados, sem casos ignorados. A execução usou cópias temporárias dos scripts e do exemplo. O primeiro ensaio encontrou uma restrição de escrita na pasta temporária do sandbox; a validação foi concluída usando uma pasta temporária dentro do workspace. Nenhuma elevação de privilégio foi necessária.

## Evidência demonstrativa

O arquivo [EXECUCAO.txt](EXECUCAO.txt) registra os comandos de criptografia e descriptografia em uma cópia de demonstração. Ele mostra os caminhos relativos e o hash do conteúdo, sem incluir a chave.

O pacote para publicação não contém a chave nem os arquivos gerados nessa execução. Esses resultados permanecem separados do material de entrega.

## Limitações

O exercício não processa arquivos arbitrários, pastas inteiras ou dados pessoais. A chave é armazenada localmente para fins didáticos; a implementação não fornece gestão de chaves de produção ou garantia de recuperação após perda da chave.

Os testes não constituem auditoria criptográfica da biblioteca nem auditoria completa de segurança do sistema de arquivos. Não foram simuladas corridas entre processos, interrupções de energia, falta de espaço em disco ou todos os tipos de redirecionamento do Windows. A validação registrada foi realizada no Windows; os comandos para outros sistemas são fornecidos, sem afirmar testes nessas plataformas.

## Aprendizados

Criptografia, autenticação e comparação de conteúdo têm papéis diferentes. A chave permite reverter a transformação; a autenticação recusa tokens inválidos; a comparação confirma que a cópia recuperada corresponde ao exemplo esperado. Preservar a entrada e recusar sobrescritas facilita observar o processo sem tornar os dados originais indisponíveis.
